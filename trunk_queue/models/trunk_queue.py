from odoo import models, fields
import requests
from requests import RequestException, HTTPError, ConnectionError
from requests.exceptions import ProxyError, SSLError, Timeout, ConnectTimeout, ReadTimeout
import datetime
import json
from odoo.tools import date_utils
import logging

from ..helper.trunk_queue_enum import TaskType, Status

_logger = logging.getLogger(__name__)


class TrunkQueue(models.Model):
    _name = 'trunk.queue'
    _description = 'Trunk Queue'

    task_type = fields.Selection([
        (TaskType.new_sale_order_production.name, 'New sale order production'),
        (TaskType.confirmed_purchase_order_production.name, 'Confirmed purchase order production')],
        default=TaskType.new_sale_order_production.name, required=True)
    attempt_count = fields.Integer("Attempt count", required=True, default=0)
    res_model = fields.Char()
    res_id = fields.Integer()
    res_name = fields.Char()
    status = fields.Selection([
        (Status.new.name, 'New'),
        (Status.processed.name, 'Processed'),
        (Status.failed.name, 'Failed')], "Status",
        default=Status.new.name, required=True)
    completed_timestamp = fields.Datetime(string="Completed timestamp", required=False)
    request_payload = fields.Text()

    def create_queue_item(self, task_type: TaskType, res_model: str, res_id: int, res_name: str):
        queue_item = {
            'task_type': task_type.name,
            'res_model': res_model,
            'res_id': res_id,
            'res_name': res_name
        }
        self.create(queue_item)

    def process_new_sale_order_production(self):
        endpoint = '/Order/NewSaleOrderProduction'

        jobs = self._get_jobs(TaskType.new_sale_order_production)
        for job in jobs:
            # get sale order
            sale_order = self.env['sale.order'].browse(job.res_id)
            sale_order_shop = self.env['sale.order'].search([('name', '=', sale_order.origin_sales_order_no)])

            raw_sale_order = sale_order.read()[0]
            if sale_order_shop:
                raw_sale_order_shop = sale_order_shop.read()[0]
            else:
                raw_sale_order_shop = False

            raw_data = {'order': raw_sale_order, 'shopOrder': raw_sale_order_shop}
            self._process_event(job, endpoint, raw_data)

    def process_confirmed_purchase_order_production(self):
        endpoint = '/PurchaseOrder/PurchaseOrderConfirmed'

        jobs = self._get_jobs(TaskType.confirmed_purchase_order_production)
        for job in jobs:
            purchase_order = self.env['purchase.order'].browse(job.res_id)
            raw_purchase_order = purchase_order.read()[0]
            raw_purchase_order['partner_id_ref'] = purchase_order.partner_id.ref
            self._process_event(job, endpoint, raw_purchase_order)

    def _process_event(self, job, endpoint, raw_data):
        job.attempt_count += 1
        payload = json.dumps(raw_data, default=date_utils.json_default)
        job.request_payload = payload
        self._process_request(job, "POST", endpoint, payload)

    def _process_request(self, job, method: str, endpoint: str, payload: str):
        base_endpoint = self._get_base_endpoint()
        headers = self._get_default_headers()
        response = False
        try:
            response = requests.request(method, base_endpoint + endpoint, headers=headers, data=payload)
        except (RequestException, HTTPError, ConnectionError, ProxyError, SSLError, Timeout, ConnectTimeout, ReadTimeout) as error:
            _logger.error(f'Could not post to Trunk. Error: {error}')

        self._process_response(job, response)

    @staticmethod
    def _process_response(job, response):
        if response and response.status_code == 200:
            job.status = Status.processed.name
            job.completed_timestamp = datetime.datetime.now()
        elif job.attempt_count >= 10:
            job.status = Status.failed.name
            job.completed_timestamp = datetime.datetime.now()

    def _get_default_headers(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        headers = {
            'ApiKey': ir_config_parameter.get_param('strai.trunk_password'),
            'ApiClient': ir_config_parameter.get_param('strai.trunk_username'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return headers

    def _get_base_endpoint(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        trunk_endpoint = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        return trunk_endpoint.endpoint

    def _get_jobs(self, task_type: TaskType):
        jobs = self.env['trunk.queue'].search([('task_type', '=', task_type.name), ('status', '=', Status.new.name)])
        return jobs
