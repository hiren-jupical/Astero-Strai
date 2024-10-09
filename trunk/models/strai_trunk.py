from odoo import models, fields, api, _
import requests
import logging

_logger = logging.getLogger(__name__)


class StraiTrunk(models.TransientModel):
    _name = 'strai.trunk'
    _description = 'Trunk Connection'

    def _get_trunk_url(self, endpoint):
        """
        Generate necessary headers for Trunk communication
        :param endpoint: Endpoint after the base URL, which we need to connect to
        :return: The full URL to connect to
        """
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        operation_mode = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        if operation_mode.endpoint:
            return operation_mode.endpoint + endpoint
        else:
            return endpoint

    def _get_headers(self):
        """
        Generate necessary headers for Trunk communication
        """
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        api_client = ir_config_parameter.get_param('strai.trunk_username')
        api_key = ir_config_parameter.get_param('strai.trunk_password')

        if isinstance(api_client, str) and isinstance(api_key, str):
            return {
                'Content-Type': 'application/json',
                'ApiClient': api_client,
                'ApiKey': api_key
            }
        else:
            _logger.error('ApiClient and ApiKey must be strings.')
            return {}

    def get_data_from_trunk(self, endpoint, data=False):
        """
        Send a GET request to Trunk, passing optional data to the endpoint
        :param endpoint: The Endpoint to connec to
        :param data: The data dict to pass to Trunk
        :return: Response data as JSON or False if there is an error
        """
        headers = self._get_headers()
        response = requests.get(self._get_trunk_url(endpoint), json=data, headers=headers) if data else requests.get(self._get_trunk_url(endpoint), headers=headers)
        if response.status_code not in [200, 201, 204]:
            # We might have an error
            _logger.error('Response from Trunk (Status {}): {}'.format(response.status_code, response.text))
            return False
        else:
            # we should have a valid response to process
            return response.json()

    def post_data_to_trunk(self, endpoint, data=False):
        """
        Send a POST request to Trunk, passing optional data to the endpoint
        :param endpoint: The Endpoint to connec to
        :param data: The data dict to pass to Trunk
        :return: Response data as JSON or False if there is an error
        """
        headers = self._get_headers()
        response = requests.post(self._get_trunk_url(endpoint), json=data, headers=headers) if data else requests.post(self._get_trunk_url(endpoint), headers=headers)
        if response.status_code not in [200, 201, 204]:
            # We might have an error
            _logger.error('Response from Trunk (Status {}): {}'.format(response.status_code, response.text))
            return False
        else:
            # we should have a valid response to process
            return response.json()

    def delete_data_in_trunk(self, endpoint, data=False):
        """
        Send a DELETE request to Trunk, passing optional data to the endpoint
        :param endpoint: The Endpoint to connec to
        :param data: The data dict to pass to Trunk
        :return: Response data as JSON or False if there is an error
        """
        headers = self._get_headers()
        response = requests.delete(self._get_trunk_url(endpoint), json=data, headers=headers) if data else requests.delete(self._get_trunk_url(endpoint), headers=headers)
        if response.status_code not in [200, 201, 204]:
            # We might have an error
            _logger.error('Response from Trunk (Status {}): {}'.format(response.status_code, response.text))
            return False
        else:
            # we should have a valid response to process
            return response.status_code
