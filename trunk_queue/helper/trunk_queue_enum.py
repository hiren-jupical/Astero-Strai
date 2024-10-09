from enum import Enum


class TaskType(Enum):
    new_sale_order_production = 'new_sale_order_production'
    confirmed_purchase_order_production = 'confirmed_purchase_order_production'


class Status(Enum):
    new = 'new'
    processed = 'processed'
    failed = 'failed'
