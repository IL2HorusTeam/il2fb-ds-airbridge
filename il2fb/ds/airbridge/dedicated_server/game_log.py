# coding: utf-8

import logging
import threading

from typing import Callable

from il2fb.commons.events import Event, EventParsingException

from il2fb.ds.airbridge.typing import EventHandler
from il2fb.ds.airbridge.typing import StringOrNoneProducer, StringHandler


LOG = logging.getLogger(__name__)


class GameLogWorker:

    def __init__(
        self,
        string_producer: StringOrNoneProducer,
        string_parser: Callable[[str], Event],
    ):
        self._string_producer = string_producer
        self._string_parser = string_parser

        self._events_subscribers = []
        self._events_subscribers_lock = threading.Lock()

        self._not_parsed_strings_subscribers = []
        self._not_parsed_strings_subscribers_lock = threading.Lock()

    def subscribe_to_events(self, subscriber: EventHandler) -> None:
        with self._events_subscribers_lock:
            self._events_subscribers.append(subscriber)

    def unsubscribe_from_events(self, subscriber: EventHandler) -> None:
        with self._events_subscribers_lock:
            self._events_subscribers.remove(subscriber)

    def subscribe_to_not_parsed_strings(
        self,
        subscriber: StringHandler,
    ) -> None:
        with self._not_parsed_strings_subscribers_lock:
            self._not_parsed_strings_subscribers.append(subscriber)

    def unsubscribe_from_not_parsed_strings(
        self,
        subscriber: StringHandler,
    ) -> None:
        with self._not_parsed_strings_subscribers_lock:
            self._not_parsed_strings_subscribers.remove(subscriber)

    def run(self) -> None:
        try:
            LOG.info("game log worker has started")
            self._run()
        except Exception:
            LOG.error("game log worker has terminated")
            raise
        else:
            LOG.info("game log worker has finished")

    def _run(self) -> None:
        while True:
            try:
                string = self._string_producer()
            except Exception:
                LOG.exception("failed to get game log string")
                continue

            if string is None:
                break

            try:
                event = self._string_parser(string)
                if event is not None:
                    self._handle_event(event)
            except EventParsingException:
                self._handle_not_parsed_string(string)
            except Exception:
                LOG.exception(f"failed to parse game log string `{string}`")

    def _handle_event(self, event: Event) -> None:
        with self._events_subscribers_lock:
            for subscriber in self._events_subscribers:
                try:
                    subscriber(event)
                except Exception:
                    LOG.exception(
                        f"subscriber {subscriber} failed to handle game log "
                        f"event {event}"
                    )

    def _handle_not_parsed_string(self, s: str) -> None:
        with self._not_parsed_strings_subscribers_lock:
            for subscriber in self._not_parsed_strings_subscribers:
                try:
                    subscriber(s)
                except Exception:
                    LOG.exception(
                        f"subscriber {subscriber} failed to handle not parsed "
                        f"game log string `{s}`"
                    )
