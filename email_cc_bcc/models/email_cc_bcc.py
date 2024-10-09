import base64
import logging
import psycopg2
import re
import threading


from odoo import api, fields, models, registry, SUPERUSER_ID, Command, _
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _get_default_knk_reply_to(self):
        current_model = self._context.get('default_model')
        current_id = self._context.get('default_res_id') 

        # order_email = self.env['res.partner'].search([('ref', '=', 'ORDREMAILEN')],limit=1).email
        # purchase_email= self.env['res.partner'].search([('ref', '=', 'INNKJOPSMAILEN')],limit=1).email
        catchall_email = 'catchall@strai.no'

        if current_model == "sale.order":
            if current_id:
                sale_order = self.env['sale.order'].search([('id', '=', current_id)],limit=1)
                if sale_order:
                    if not sale_order.is_production:
                        return f'{sale_order.user_id.partner_id.email};{catchall_email}'
        
        elif current_model == "purchase.order":
            if current_id:
                purchase_order = self.env['purchase.order'].search([('id', '=', current_id)],limit=1)
                if purchase_order and not purchase_order.is_production:
                    return f'{purchase_order.user_id.partner_id.email};{catchall_email}'
        elif current_model == "account.move":
            if current_id:
                account_move_record = self.env['account.move'].search([('id', '=', current_id)],limit=1)
                if account_move_record and account_move_record.company_id.id == 7 and account_move_record.company_id.invoice_sender_email: #designated logic for KRS
                    return f'{account_move_record.company_id.invoice_sender_email};{catchall_email}'
                elif    account_move_record and account_move_record.move_type in ['out_invoice', 'out_refund'] and  \
                        account_move_record.company_id.production == False and not \
                        account_move_record.invoice_user_id.company_id.production:
                    return f'{account_move_record.invoice_user_id.partner_id.email};{catchall_email}'

    knk_reply_to = fields.Char(string="Reply To", default=_get_default_knk_reply_to)

    def get_mail_values(self, res_ids):
        res = super(MailComposer, self).get_mail_values(res_ids)
        for key, value in res.items():
            if self.knk_reply_to:
                value['reply_to'] = self.knk_reply_to
        return res


# class MailMail(models.Model):
#     _inherit = 'mail.mail'
#
#     def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
#         IrMailServer = self.env['ir.mail_server']
#         IrAttachment = self.env['ir.attachment']
#         for mail_id in self.ids:
#             success_pids = []
#             failure_type = None
#             # processing_pid = None
#             mail = None
#             try:
#                 mail = self.browse(mail_id)
#                 if mail.state != 'outgoing':
#                     if mail.state != 'exception' and mail.auto_delete:
#                         mail.sudo().unlink()
#                     continue
#
#                 # remove attachments if user send the link with the access_token
#                 body = mail.body_html or ''
#                 attachments = mail.attachment_ids
#                 for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
#                     attachments = attachments - IrAttachment.browse(int(link))
#
#                 # load attachment binary data with a separate read(), as prefetching all
#                 # `datas` (binary field) could bloat the browse cache, triggerring
#                 # soft/hard mem limits with temporary data.
#                 attachments = [(a['name'], base64.b64decode(a['datas']), a['mimetype'])
#                                for a in attachments.sudo().read(['name', 'datas', 'mimetype']) if a['datas'] is not False]
#
#                 # specific behavior to customize the send email for notified partners
#                 email_list = []
#                 if mail.email_to:
#                     email_list.append(mail._send_prepare_values())
#                 for partner in mail.recipient_ids:
#                     values = mail._send_prepare_values(partner=partner)
#                     values['partner_id'] = partner
#                     email_list.append(values)
#
#                 # headers
#                 headers = {}
#                 ICP = self.env['ir.config_parameter'].sudo()
#                 bounce_alias = ICP.get_param("mail.bounce.alias")
#                 catchall_domain = ICP.get_param("mail.catchall.domain")
#                 if bounce_alias and catchall_domain:
#                     if mail.mail_message_id.is_thread_message():
#                         headers['Return-Path'] = '%s+%d-%s-%d@%s' % (bounce_alias, mail.id, mail.model, mail.res_id, catchall_domain)
#                     else:
#                         headers['Return-Path'] = '%s+%d@%s' % (bounce_alias, mail.id, catchall_domain)
#                 if mail.headers:
#                     try:
#                         headers.update(safe_eval(mail.headers))
#                     except Exception:
#                         pass
#
#                 # Writing on the mail object may fail (e.g. lock on user) which
#                 # would trigger a rollback *after* actually sending the email.
#                 # To avoid sending twice the same email, provoke the failure earlier
#                 mail.write({
#                     'state': 'exception',
#                     'failure_reason': _('Error without exception. Probably due do sending an email without computed recipients.'),
#                 })
#                 # Update notification in a transient exception state to avoid concurrent
#                 # update in case an email bounces while sending all emails related to current
#                 # mail record.
#                 notifs = self.env['mail.notification'].search([
#                     ('notification_type', '=', 'email'),
#                     ('mail_mail_id', 'in', mail.ids),
#                     ('notification_status', 'not in', ('sent', 'canceled'))
#                 ])
#                 if notifs:
#                     notif_msg = _('Error without exception. Probably due do concurrent access update of notification records. Please see with an administrator.')
#                     notifs.sudo().write({
#                         'notification_status': 'exception',
#                         'failure_type': 'unknown',
#                         'failure_reason': notif_msg,
#                     })
#                     # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
#                     # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
#                     notifs.flush(fnames=['notification_status', 'failure_type', 'failure_reason'], records=notifs)
#
#                 # build an RFC2822 email.message.Message object and send it without queuing
#                 res = None
#                 for email in email_list:
#                     msg = IrMailServer.build_email(
#                         email_from=mail.email_from,
#                         email_to=email.get('email_to'),
#                         subject=mail.subject,
#                         body=email.get('body'),
#                         body_alternative=email.get('body_alternative'),
#                         email_cc=tools.email_split(mail.email_cc),
#                         reply_to=mail.reply_to,
#                         attachments=attachments,
#                         message_id=mail.message_id,
#                         references=mail.references,
#                         object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
#                         subtype='html',
#                         subtype_alternative='plain',
#                         headers=headers)
#                     processing_pid = email.pop("partner_id", None)
#                     try:
#                         res = IrMailServer.send_email(
#                             msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
#                         if processing_pid:
#                             success_pids.append(processing_pid)
#                     except AssertionError as error:
#                         if str(error) == IrMailServer.NO_VALID_RECIPIENT:
#                             failure_type = "RECIPIENT"
#                             # No valid recipient found for this particular
#                             # mail item -> ignore error to avoid blocking
#                             # delivery to next recipients, if any. If this is
#                             # the only recipient, the mail will show as failed.
#                             _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
#                                          mail.message_id, email.get('email_to'))
#                         else:
#                             raise
#                 if res:  # mail has been sent at least once, no major exception occured
#                     mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
#                     _logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
#                     # /!\ can't use mail.state here, as mail.refresh() will cause an error
#                     # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
#                 mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
#             except MemoryError:
#                 # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
#                 # instead of marking the mail as failed
#                 _logger.exception(
#                     'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
#                     mail.id, mail.message_id)
#                 # mail status will stay on ongoing since transaction will be rollback
#                 raise
#             except (psycopg2.Error, smtplib.SMTPServerDisconnected):
#                 # If an error with the database or SMTP session occurs, chances are that the cursor
#                 # or SMTP session are unusable, causing further errors when trying to save the state.
#                 _logger.exception(
#                     'Exception while processing mail with ID %r and Msg-Id %r.',
#                     mail.id, mail.message_id)
#                 raise
#             except Exception as e:
#                 failure_reason = tools.ustr(e)
#                 _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
#                 mail.write({'state': 'exception', 'failure_reason': failure_reason})
#                 mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason, failure_type='UNKNOWN')
#                 if raise_exception:
#                     if isinstance(e, (AssertionError, UnicodeEncodeError)):
#                         if isinstance(e, UnicodeEncodeError):
#                             value = "Invalid text: %s" % e.object
#                         else:
#                             # get the args of the original error, wrap into a value and throw a MailDeliveryException
#                             # that is an except_orm, with name and value as arguments
#                             value = '. '.join(e.args)
#                         raise MailDeliveryException(_("Mail Delivery Failed"), value)
#                     raise
#
#             if auto_commit is True:
#                 self._cr.commit()
#         return True


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_record_by_email(self, message, recipients_data, msg_vals=False,
                                model_description=False, mail_auto_delete=True, check_existing=False,
                                force_send=True, send_after_commit=True,
                                **kwargs):
        """ Method to send email linked to notified messages.

        :param message: mail.message record to notify;
        :param recipients_data: see ``_notify_thread``;
        :param msg_vals: see ``_notify_thread``;

        :param model_description: model description used in email notification process
          (computed if not given);
        :param mail_auto_delete: delete notification emails once sent;
        :param check_existing: check for existing notifications to update based on
          mailed recipient, otherwise create new notifications;

        :param force_send: send emails directly instead of using queue;
        :param send_after_commit: if force_send, tells whether to send emails after
          the transaction has been committed using a post-commit hook;
        """
        partners_data = [r for r in recipients_data if r['notif'] == 'email']
        if not partners_data:
            return True

        model = msg_vals.get('model') if msg_vals else message.model
        model_name = model_description or (self._fallback_lang().env['ir.model']._get(model).display_name if model else False) # one query for display name
        recipients_groups_data = self._notify_classify_recipients(partners_data, model_name, msg_vals=msg_vals)

        if not recipients_groups_data:
            return True
        force_send = self.env.context.get('mail_notify_force_send', force_send)

        template_values = self._notify_prepare_template_context(message, msg_vals, model_description=model_description) # 10 queries

        email_layout_xmlid = msg_vals.get('email_layout_xmlid') if msg_vals else message.email_layout_xmlid
        template_xmlid = email_layout_xmlid if email_layout_xmlid else 'mail.message_notification_email'
        try:
            base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(lang=template_values['lang']) # 1 query
        except ValueError:
            _logger.warning('QWeb template %s not found when sending notification emails. Sending without layouting.' % (template_xmlid))
            base_template = False

        mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name) # in cache, no queries
        # Replace new lines by spaces to conform to email headers requirements
        mail_subject = ' '.join((mail_subject or '').splitlines())
        # prepare notification mail values
        base_mail_values = {
            'mail_message_id': message.id,
            'mail_server_id': message.mail_server_id.id, # 2 query, check acces + read, may be useless, Falsy, when will it be used?
            'auto_delete': mail_auto_delete,
            # due to ir.rule, user have no right to access parent message if message is not published
            'references': message.parent_id.sudo().message_id if message.parent_id else False,
            'subject': mail_subject,
        }
        base_mail_values = self._notify_by_email_add_values(base_mail_values)

        headers = self._notify_email_headers()
        if headers:
            base_mail_values['headers'] = headers

        # Clean the context to get rid of residual default_* keys that could cause issues during
        # the mail.mail creation.
        # Example: 'default_state' would refer to the default state of a previously created record
        # from another model that in turns triggers an assignation notification that ends up here.
        # This will lead to a traceback when trying to create a mail.mail with this state value that
        # doesn't exist.
        SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self._context))
        SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self._context))
        emails = self.env['mail.mail'].sudo()

        # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
        notif_create_values = []
        recipients_max = 50
        for recipients_group_data in recipients_groups_data:
            # generate notification email content
            recipients_ids = recipients_group_data.pop('recipients')
            render_values = {**template_values, **recipients_group_data}
            # {company, is_discussion, lang, message, model_description, record, record_name, signature, subtype, tracking_values, website_url}
            # {actions, button_access, has_button_access, recipients}

            if base_template:
                mail_body = base_template._render(render_values, engine='ir.qweb', minimal_qcontext=True)
            else:
                mail_body = message.body
            mail_body = self.env['mail.render.mixin']._replace_local_links(mail_body)

            # create email
            for recipients_ids_chunk in split_every(recipients_max, recipients_ids):
                recipient_values = self._notify_email_recipient_values(recipients_ids_chunk)
                email_to = recipient_values['email_to']
                recipient_ids = recipient_values['recipient_ids']

                create_values = {
                    'body_html': mail_body,
                    'subject': mail_subject,
                    'recipient_ids': [Command.link(pid) for pid in recipient_ids],
                }
                if email_to:
                    create_values['email_to'] = email_to
                create_values.update(base_mail_values)  # mail_message_id, mail_server_id, auto_delete, references, headers
                email = SafeMail.create(create_values)

                if email and recipient_ids:
                    tocreate_recipient_ids = list(recipient_ids)
                    if check_existing:
                        existing_notifications = self.env['mail.notification'].sudo().search([
                            ('mail_message_id', '=', message.id),
                            ('notification_type', '=', 'email'),
                            ('res_partner_id', 'in', tocreate_recipient_ids)
                        ])
                        if existing_notifications:
                            tocreate_recipient_ids = [rid for rid in recipient_ids if rid not in existing_notifications.mapped('res_partner_id.id')]
                            existing_notifications.write({
                                'notification_status': 'ready',
                                'mail_mail_id': email.id,
                            })
                    notif_create_values += [{
                        'mail_message_id': message.id,
                        'res_partner_id': recipient_id,
                        'notification_type': 'email',
                        'mail_mail_id': email.id,
                        'is_read': True,  # discard Inbox notification
                        'notification_status': 'ready',
                    } for recipient_id in tocreate_recipient_ids]
                emails |= email

        if notif_create_values:
            SafeNotification.create(notif_create_values)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.currentThread(), 'testing', False)
        if force_send and len(emails) < recipients_max and (not self.pool._init or test_mode):
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                email_ids = emails.ids
                dbname = self.env.cr.dbname
                _context = self._context

                @self.env.cr.postcommit.add
                def send_notifications():
                    db_registry = registry(dbname)
                    with db_registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, _context)
                        env['mail.mail'].browse(email_ids).send()
            else:
                emails.send()

        return True

    @api.model
    def _message_route_process(self, message, message_dict, routes):
        self = self.with_context(attachments_mime_plainxml=True) # import XML attachments as text
        # postpone setting message_dict.partner_ids after message_post, to avoid double notifications
        original_partner_ids = message_dict.pop('partner_ids', [])
        thread_id = False
        for model, thread_id, custom_values, user_id, alias in routes or ():
            subtype_id = False
            related_user = self.env['res.users'].browse(user_id)
            Model = self.env[model].with_context(mail_create_nosubscribe=True, mail_create_nolog=True)
            if not (thread_id and hasattr(Model, 'message_update') or hasattr(Model, 'message_new')):
                raise ValueError(
                    "Undeliverable mail with Message-Id %s, model %s does not accept incoming emails" %
                    (message_dict['message_id'], model)
                )

            # disabled subscriptions during message_new/update to avoid having the system user running the
            # email gateway become a follower of all inbound messages
            ModelCtx = Model.with_user(related_user).sudo()
            if thread_id and hasattr(ModelCtx, 'message_update'):
                thread = ModelCtx.browse(thread_id)
                thread.message_update(message_dict)
            else:
                # if a new thread is created, parent is irrelevant
                message_dict.pop('parent_id', None)
                thread = ModelCtx.message_new(message_dict, custom_values)
                thread_id = thread.id
                subtype_id = thread._creation_subtype().id

            # replies to internal message are considered as notes, but parent message
            # author is added in recipients to ensure he is notified of a private answer
            parent_message = False
            if message_dict.get('parent_id'):
                parent_message = self.env['mail.message'].sudo().browse(message_dict['parent_id'])
            partner_ids = []
            if not subtype_id:
                if message_dict.get('is_internal'):
                    subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
                    if parent_message and parent_message.author_id:
                        partner_ids = [parent_message.author_id.id]
                else:
                    subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')

            post_params = dict(subtype_id=subtype_id, partner_ids=partner_ids, **message_dict)
            # remove computational values not stored on mail.message and avoid warnings when creating it
            for x in ('from', 'to', 'recipients', 'references', 'in_reply_to', 'bounced_email', 'bounced_message', 'bounced_msg_id', 'bounced_partner'):
                post_params.pop(x, None)
            # new_msg = False
            if thread._name == 'mail.thread':  # message with parent_id not linked to record
                new_msg = thread.message_notify(**post_params)
            else:
                # parsing should find an author independently of user running mail gateway, and ensure it is not odoobot
                partner_from_found = message_dict.get('author_id') and message_dict['author_id'] != self.env['ir.model.data']._xmlid_to_res_id('base.partner_root')
                thread = thread.with_context(mail_create_nosubscribe=not partner_from_found)
                new_msg = thread.message_post(**post_params)

            if new_msg and original_partner_ids:
                # postponed after message_post, because this is an external message and we don't want to create
                # duplicate emails due to notifications
                new_msg.write({'partner_ids': original_partner_ids})
        return thread_id

    # No custom code available, so commenting the method in custom
    # @api.returns('mail.message', lambda value: value.id)
    # def message_post(self, *,
    #                  body='', subject=None, message_type='notification',
    #                  email_from=None, author_id=None, parent_id=False,
    #                  subtype_xmlid=None, subtype_id=False, partner_ids=None,
    #                  attachments=None, attachment_ids=None,
    #                  add_sign=True,
    #                  record_name=False,
    #                  **kwargs):

    #     new_message = super(MailThread, self).message_post(
    #                  body=body, subject=subject, message_type=message_type,
    #                  email_from=email_from, author_id=author_id, parent_id=parent_id,
    #                  subtype_xmlid=subtype_xmlid, subtype_id=subtype_id, partner_ids=partner_ids,
    #                  attachments=attachments, attachment_ids=attachment_ids,
    #                  add_sign=add_sign,
    #                 record_name=record_name,
    #                  **kwargs)
    #     return new_message
