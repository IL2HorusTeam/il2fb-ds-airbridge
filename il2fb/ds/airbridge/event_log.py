# coding: utf-8

import logging
import threading

from typing import Callable

from il2fb.parsers.events.events import Event
from il2fb.parsers.events.exceptions import EventParsingError

from .typing import EventOrNone, EventHandler
from .typing import StringOrNoneProducer, StringHandler


LOG = logging.getLogger(__name__)


class EventLogWorker:

    def __init__(
        self,
        string_producer: StringOrNoneProducer,
        string_parser: Callable[[str], EventOrNone],
    ):
        self._string_producer = string_producer
        self._string_parser = string_parser

        self._do_stop = False
        self._stop_lock = threading.Lock()

        self._events_subscribers = []
        self._events_subscribers_lock = threading.Lock()

        self._errors_subscribers = []
        self._errors_subscribers_lock = threading.Lock()

    def subscribe_to_events(self, subscriber: EventHandler) -> None:
        with self._events_subscribers_lock:
            self._events_subscribers.append(subscriber)

    def unsubscribe_from_events(self, subscriber: EventHandler) -> None:
        with self._events_subscribers_lock:
            self._events_subscribers.remove(subscriber)

    def subscribe_to_errors(self, subscriber: StringHandler) -> None:
        with self._errors_subscribers_lock:
            self._errors_subscribers.append(subscriber)

    def unsubscribe_from_errors(self, subscriber: StringHandler) -> None:
        with self._errors_subscribers_lock:
            self._errors_subscribers.remove(subscriber)

    def stop(self) -> None:
        """
        Ask worker to stop.

        Actual stop will happen only after string producer will produce
        ``None`` value.

        """
        with self._stop_lock:
            self._do_stop = False

    def run(self) -> None:
        try:
            LOG.info("event log worker has started")
            self._run()
        except Exception:
            LOG.error("event log worker has terminated")
            raise
        else:
            LOG.info("event log worker has finished")

    def _run(self) -> None:
        while True:
            try:
                string = self._string_producer()
            except Exception:
                LOG.exception("failed to get event log string")
                continue

            if string is None:
                with self._stop_lock:
                    if self._do_stop:
                        break
                    else:
                        continue

            try:
                event = self._string_parser(string)
                if event is not None:
                    self._handle_event(event)
            except EventParsingError:
                self._handle_error(string)
            except Exception:
                LOG.exception(f"failed to parse event log string `{string}`")

    def _handle_event(self, event: Event) -> None:
        with self._events_subscribers_lock:
            for subscriber in self._events_subscribers:
                try:
                    subscriber(event)
                except Exception:
                    LOG.exception(
                        f"subscriber {subscriber} failed to handle log "
                        f"event {event}"
                    )

    def _handle_error(self, s: str) -> None:
        with self._errors_subscribers_lock:
            for subscriber in self._errors_subscribers:
                try:
                    subscriber(s)
                except Exception:
                    LOG.exception(
                        f"subscriber {subscriber} failed to handle invalid "
                        f"event log string `{s}`"
                    )
