# -*- coding: utf-8 -*-
##############################################################################
#
#    Flyt Consulting AS
#    Copyright (C) 2018-TODAY Flyt Consulting AS(<http://www.flytconsulting.no>).
#    Author: Flyt Consulting AS(<http://www.flytconsulting.no>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Mail follower notification configuration",
    "summary": "Choose to notify followers on mail.compose.message",
    "author":"Flyt Consulting AS",
    'website': 'https://www.flytconsulting.no',  
    "category": "Social Network",
    'version': '17.0.1.0.0',
    'license': 'OPL-1',
    "depends": ["mail","account"],
    "data": [
            "wizard/mail_compose_message_view.xml",
             "wizard/account_invocie_send.xml",
             ],
}
