# file:/app/superset/reports/notifications/webhook.py
import json
import logging
import textwrap
import requests
import base64
from dataclasses import dataclass
from email.utils import make_msgid, parseaddr
from typing import Any, Optional

from flask_babel import gettext as __

from superset import app
from superset.exceptions import SupersetErrorsException
from superset.reports.models import ReportRecipientType
from superset.reports.notifications.base import BaseNotification
from superset.reports.notifications.exceptions import NotificationError
from superset.utils.core import HeaderDataType, send_email_smtp
from superset.utils.decorators import statsd_gauge

logger = logging.getLogger(__name__)


@dataclass
class WebhookContent:
    body: str
    header_data: Optional[HeaderDataType] = None
    data: Optional[dict[str, Any]] = None
    images: Optional[dict[str, bytes]] = None


class WebhookNotification(BaseNotification):  # pylint: disable=too-few-public-methods
    """
    Calls webhook for a report recipient
    """

    type = ReportRecipientType.WEBHOOK


    @staticmethod
    def _error_template(text: str) -> str:
        return __(
            """
            Error: %(text)s
            """,
            text=text,
        )

    def _get_content(self) -> WebhookContent:
        if self._content.text:
            return WebhookContent(body=self._error_template(self._content.text))
        # Get the domain from the 'From' address ..
        # and make a message id without the < > in the end
        csv_data = None
        images = {}

        if self._content.screenshots:
            images = [
                base64.b64encode(screenshot).decode('ascii')
                for screenshot in self._content.screenshots
            ]

        if self._content.csv:
            csv_data = {__("%(name)s.csv", name=self._content.name): self._content.csv}
        return WebhookContent(
            images=images,
            data=csv_data,
            body=None,
            header_data=self._content.header_data,
        )

    def _get_subject(self) -> str:
        return __(
            "%(prefix)s %(title)s",
            prefix=app.config["EMAIL_REPORTS_SUBJECT_PREFIX"],
            title=self._content.name,
        )

    def _get_to(self) -> str:
        return json.loads(self._recipient.recipient_config_json)["target"]

    @statsd_gauge("reports.webhook.send")
    def send(self) -> None:
       subject = self._get_subject()
       content = self._get_content()
       to = self._get_to()


       headers = {
       }

       payload = {
          'subject': subject,
          'content': {
             #'header_data': content.header_data,
             'body': content.body,
             'data': content.data,
             'images': content.images,
          }
       }

       try:
          response = requests.post(to, headers=headers, data=json.dumps(payload), timeout=30)
          response.raise_for_status()
          logger.info("Report sent to webhook, notification content is %s, url:%s, status scode:%d", content.header_data, to, response.status_code)
       except requests.exceptions.HTTPError as ex:
          raise NotificationError(f"HTTP error occurred: {ex}") from ex
       except Exception as ex:
          raise NotificationError(f"An error occurred: {ex}") from ex