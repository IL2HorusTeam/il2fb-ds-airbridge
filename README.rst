IL-2 FB Dedicated Server Airbridge
##################################

|pypi_package| |python_versions| |license| |maintainability| |codebeat| |codacy| |scrutinizer|

|logo|


**Table of Contents**

.. contents::
    :local:
    :depth: 3
    :backlinks: none


Glossary
========

Definitions below give explanation of terms used in this text. Some
explanations may slightly differ from generally-accepted because of
domain-specific aspects.

IL-2 FB
    "Old" version of «IL-2 Sturmovik» aviasimulator. It is often referenced
    as «IL-2 Sturmovik: Forgotten Battles», however it also implies all
    further commercial versions up to «IL-2 Sturmovik: 1946» including all
    official free patches.

DS
    Dedicated server of IL-2 FB: a stand-alone headless application which is
    used for creation of a single entry point for multiplayer game mode.

API
    Application's interface which makes it possible for 3rd-party software to
    interact with the application.

Telnet
    A network protocol which provides a bidirectional interactive text-oriented
    communication facility using a virtual terminal connection.

Console
    Server's terminal (shell) which is used by server's administrators to
    manage server by executing text commands and to monitor several aspects of
    users' activity like connections to DS, chat messages and so on. Console
    is also an API served by server over Telnet protocol to provide terminal
    access to 3rd-party software.

Device Link
    A game-specific network protocol and API which is generally used to access
    current state of players' aircrafts by 3rd-party software. For DS it
    provides ability to query coorinates of all actors and static objects in
    nearly real-time fashion. `Refer to documentation <https://docs.google.com/document/d/1mIAa-sMQhLFyHgDdRpABwFZ9TW0Yxcwr9Lc2jTmTGtI/edit?usp=sharing>`_
    for more details.

Mission
    A text file which contains definition of game environment, objects, actors,
    targets and so on. Mission is also a process of execution of mission file,
    i.e. a running game. `Refer to demo page of mission parser <http://il2horusteam.github.io/il2fb-mission-parser/>`_
    to get example of mission definition.

Game Log
    A text file produced by DS which stores in-game events each of which is
    recorded in an append-only mode. Each event represents a set of changes
    in state of actors in mission. `Refer to demo page of game log parser <http://il2horusteam.github.io/il2fb-game-log-parser/>`_
    to get examples of event records.

Server Config
    A text file which defines server's technical characteristics, facilities
    and global game options. `Refer to configuration editor <https://il2horusteam.github.io/il2fb-ds-config/>`_
    for more details.

Streaming
    A process of continuous sharing of data from producer to direct consumer or
    storage.

Pub/Sub
    Publish–subscribe is a communication pattern where senders of messages know
    nothing about message receivers, as communication is provided by a mediator
    called "message broker" or "message bus". This pattern allows to totally
    decouple senders from receivers, hence, they do not need to know about
    existence, location, availability and implementation of each other.

HTTP
    Request–response communication protocol in the client–server computing
    model, where messages are presented as structured text. Designed for
    transfer of hypermedia text (HTML). It is the foundation of any data
    exchange on the Web.

REST
    REST (REpresentational State Transfer) is an architectural style, and an
    approach to communications that is often used in the development of Web
    services. The key abstraction of information in REST is a resource. Other
    important thing associated with REST is resource methods to be used to
    perform the desired transition of resource's state. Usually implemented on
    top of HTTP, but not limited to it.

WS
    WebSockets is a communications protocol, providing full-duplex
    communication channels between a client and a server. It makes it possible
    to send messages to a server and receive event-driven responses without
    having to poll the server for a reply. WebSockets protocol was designed to
    work over HTTP and allows web application to communicate with server
    directly from web browser.

NATS
    NATS is a high performance messaging system that acts as a distributed
    messaging queue for cloud native applications
    (`see more info <http://nats.io>`_).

NATS Streaming
    NATS Streaming is a data streaming system powered by NATS
    (`see more info <https://nats.io/documentation/streaming/nats-streaming-intro/>`_).


Synopsis
========

Airbridge is an application which wraps dedicated server of
«IL-2 Sturmovik: Forgotten Battles» aviasimulator.

It acts as additional access layer on top of dedicated server and provides
high-level API with ability to subscribe to game events. Airbridge makes it
possible to communicate with dedicated server by exchanging structured messages
instead of raw strings and packages.

This means that you can access server's console, device link and mission
storage in a unified way. Also it's possible to subscribe to the stream of
parsed game events easily.

Airbridge allows totally remote access to dedicated server without need to
bother about access to server's file system. This allows to escape limitations
on location of supplementary software and server commanders: dedicated server
and 3rd-party software can now run on different machines and under different
operating systems.

All that brings much easier server's API and more pleasant development
experience.


Rationale
=========

The main rationale behind this project is a need for convenient unified
programmatic access to different facilities of dedicated server along with
ability to monitor users' in-game activity and to manage server remotely.

Dedicated server exposes multiple facilities to 3rd-party applications:
management console, location service, mission storage, config, streaming of
in-game events, etc. All these facilities require different ways of
communication and use different data structured for that, which are not
documented. This makes it difficult, tedious and error-prone to build systems
on top of bare dedicated server, especially server commanders. Developers of
every commander have to invent their own toolset for accessing same
server's facilities. This results in duplication of code and different
implementations for different programming languages.

Airbridge unifies API to server's facilities and uses structured messages for
communication instead of raw strings or bytes. It provides API consistency
and development comfort. Access to  each facility is done via corresponding
stand-alone library, e.g.
`il2fb-ds-middleware <https://github.com/IL2HorusTeam/il2fb-ds-middleware>`_,
`il2fb-game-log-parser <https://github.com/IL2HorusTeam/il2fb-game-log-parser>`_,
`il2fb-mission-parser <https://github.com/IL2HorusTeam/il2fb-mission-parser>`_
and `il2fb-ds-config <https://github.com/IL2HorusTeam/il2fb-ds-config>`_.
These libraries accumulate almost all knowledge of their subjects and can be
used separately. Community can contrubite to their development and free up
much of resources by reusing these libraries. Airbridge aggregates These
libraries and exposes their functionality on top of a running dedicated server.

Dedicated server allows only one application to access its management console
at a time. Moreover, storage of game events (game log) is sticked to server's
file system making it impossible to access events outside server. Same is right
for mission storage: if missions are genarated by 3rd-party software, they need
to be uploaded to server's mission storage, but there is no way to do this.
All that results into creation of heavy monolithic applications which combine
application's logic, communication with game server and external services like
databases, web applications and mission generators into a complex one-stop
shop.

Additionally, most of dedicated servers run on dedicated hardware along with
other services under Windows OS. This is quite not the best OS for running
complex systems and it's definitely not suitable for development of them.

Airbridge allows developes of 3rd-party software to escape single machine and
Windows OS giving them ability to bring more power and flexibility to
computation, logic and infrastructure of their systems.


Architecture Overview
=====================

The diagram below depicts architecture of Airbridge application for better
understanding of its implementation and work principles.

.. image:: ./docs/Overview.png
   :alt: Architecture Overview
   :align: center


Airbridge application runs dedicated server in background as a coprocess. It
captures server's STDOUT with STDIN and forwards it to own STDOUT with STDIN.
STDIN of Airbridge is forwarded to server's STDIN. This allows to do analysis
and filtering of terminal I/O, e.g. addition of colors for prompt and errors.
From user's perspective there's no visible difference between work with bare
server and work with Airbridge. This is good for compatibility reasons.

Information about server's config is provided to Airbridge by
`il2fb-ds-config <https://github.com/IL2HorusTeam/il2fb-ds-config>`_ library.
Most important config options are related to console's and device link's ports
and location of game log. Location of missions is always known and contained
inside server's directory.

Communication between Airbridge and dedicated server is provided by device link
and console clients (see `il2fb-ds-middleware <https://github.com/IL2HorusTeam/il2fb-ds-middleware>`_ library).
They allow to perform high-level requests as well as to send raw data. The
latter one is used to build appropriate proxies on top of clients. Proxies
allow existing applications to continue to communicate with server without
changes. At the same time new applications can use unified API of Airbridge
without any need to bother themselves with knowledge about low-level protocols.

Device link on dedicated server can be used only to locate coordinates of
actors and buildings. As location of objects is done by execution of multiple
requests to server's device link, a ``radar`` is build on top of its client to
simplify location of different types of objects.

Game log of dedicated server is monitored by a game log watcher. If new records
appear in game log, the watcher will read them and pass to a game log parser
(see `il2fb-game-log-parser <https://github.com/IL2HorusTeam/il2fb-game-log-parser>`_ library).
The parser emits structured representation of events. It also emits not parsed
strings if it failes to parse them. This can be used to track parsing errors
which can occur if a new or unknown event happens. Such events can be stored
and used for improving parser.

All features of dedicated server can be separated into two categories: requests
and streaming. Requests are made via radar or console client. Streaming is a
bit more compticated as events of a single logical facility can come from
different physical souces (i.e. events mainly come from game log but can come
from console client as well).

There are four logical facilities which bring streaming to their subscribers:
``chat``, ``events``, ``not parsed strings`` and ``radar``. The first three
facilities act as routers between data sources and subscribers: ``chat``
facility subscribes to chat messages from console client and broadcasts them to
chat subscribers; ``events`` facility subscribes to game events from game log
parser and to user connection events from console client and broadcasts events
to events subscribers; ``not parsed strings`` facility subscribes to strings
produced by game log parser and broadcasts them to own subscribers.
In contrast, ``radar`` facility does not route data from other sources.
Instead, it produces it by querying radar component periodically. Period of
querying depends on the needs of its subscribers.

Subscribers in terms of Airbridge are any objects who follow its subscription
interface. Subscribers can be static and dynamic: static subscribers are
created when application starts and work until it exits; dynamic subscribers
can be created and destroyed at any moment. For example, it's possible to
create a file streaming subscriber or NATS streaming subscriber which will work
from application's startup till its end. Also it's possible to connect to
Airbridge via WebSocket and subscribe to facilities dynamically.

Clients of Airbridge can perform requests via different APIs depending on their
needs. They can use Request-Reply API over NATS or REST API over HTTP.

REST API combines two independent parts: API for dedicated server and API for
missions storage. In fact, these APIs can be separated from each other and live
their independent lives in different services (splitted into microservices),
but this does not make sense at this point due to maintenance overhead.


Features Overview
=================

This section provides an overview of features which Airbridge brings to its
users. As it was already mentioned in the previous section, all features can
be devided into two categories: requests and streaming.


Requests
--------

Requests are used to query data or to change state of processes and objects.
They can have or not have responses depending on their type.

All requests which interact with dedicated server accept optional parameter
``timeout``. It has type ``float`` and is measured in seconds.

In contrast with raw server's communication interfaces, requests API of
Airbridge provides seamless multiplexing of requests comming from multiple
clients.


REST
~~~~

The following part of documentation lists and describes REST API endpoints
which are available over HTTP.

Bodies of POST requests and responses of all requests are formatted as JSON.

All endpoints accept optional ``pretty`` query parameter. For example:
``/info?pretty``. It tells endpoints to make "pretty" output by adding
indents. This can be useful for debugging.

Timeouts are passed as query parameters also, e.g.: ``/info?timeout=3``

``GET /``
    Check status of Airbridge and dedicated server. Can be useful for health
    checking and failure detection with tools like
    `Consul <https://www.consul.io>`_.

    Parameters
        No parameters.

    Responses
        ``200``
            Server is alive.

            Example
                .. code-block:: json

                    {
                        "status": "alive"
                    }

    Authorization
        No authorization.


``GET /info``
    Get information about server. Wraps ``server`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            Serialized `il2fb.ds.middleware.console.structures.ServerInfo <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/console/structures.py#L10>`_
            structure.

            Example
                .. code-block:: json

                    {
                        "type": "Local server",
                        "name": "Development server",
                        "description": "Dedicated Server for local tests",
                        "__type__": "il2fb.ds.middleware.console.structures.ServerInfo"
                    }

    Authorization
        No authorization.


``GET /humans``
    Get list of users connected to server. Wraps ``user`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.console.structures.Human <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/console/structures.py#L27>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "callsign": "john.doe",
                            "ping": 15,
                            "score": 0,
                            "belligerent": {
                                "name": "red",
                                "value": 1,
                                "verbose_name": "red",
                                "help_text": null
                            },
                            "aircraft": {
                                "designation": "* Red 1",
                                "type": "Yak-1"
                            },
                            "__type__": "il2fb.ds.middleware.console.structures.Human"
                        }
                    ]

    Authorization
        Required if configured.


``GET /humans/count``
    Get number of users connected to server. Equals to a number of records
    returned by ``user`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            Integer representing number of connected users.

            Example
                .. code-block:: json

                    7

    Authorization
        Required if configured.


``GET /humans/statistics``
    Get server's statistics for users connected to server.
    Wraps ``user STAT`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.console.structures.HumanStatistics <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/console/structures.py#L45>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "callsign": "john.doe",
                            "score": 0,
                            "state": "Landed at Airfield",
                            "enemy_aircraft_kills": 0,
                            "enemy_static_aircraft_kills": 0,
                            "enemy_tank_kills": 0,
                            "enemy_car_kills": 0,
                            "enemy_artillery_kills": 0,
                            "enemy_aaa_kills": 0,
                            "enemy_wagon_kills": 0,
                            "enemy_ship_kills": 0,
                            "enemy_radio_kills": 0,
                            "friendly_aircraft_kills": 0,
                            "friendly_static_aircraft_kills": 0,
                            "friendly_tank_kills": 0,
                            "friendly_car_kills": 0,
                            "friendly_artillery_kills": 0,
                            "friendly_aaa_kills": 0,
                            "friendly_wagon_kills": 0,
                            "friendly_ship_kills": 0,
                            "friendly_radio_kills": 0,
                            "bullets_fired": 0,
                            "bullets_hit": 0,
                            "bullets_hit_air_targets": 0,
                            "rockets_launched": 0,
                            "rockets_hit": 0,
                            "bombs_dropped": 0,
                            "bombs_hit": 0,
                            "__type__": "il2fb.ds.middleware.console.structures.HumanStatistics"
                        }
                    ]

    Authorization
        Required if configured.


``POST /humans/kick``
    Kick all users from server.

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /humans/<callsign>/kick``
    Kick user from server by user's callsign.

    Parameters
        In URL
            ``callsign``
                Callsign of user to kick.

                Type
                    ``string``

                Example
                    ``/humans/john.doe/kick``

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /chat``
    Send message in chat to everyone.

    Parameters
        In body
            ``message``
                Message to send.

                Type
                    ``string``

            Body example
                .. code-block:: json

                    {
                        "message": "hello!"
                    }

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /chat/humans/<addressee>``
    Send message in chat to a user.

    Parameters
        In URL
            ``addressee``
                Callsign of user to chat to.

                Type
                    ``string``

                Example:
                    ``/chat/humans/john.doe``

        In body
            ``message``
                Message to send.

                Type
                    ``string``

            Body example
                .. code-block:: json

                    {
                        "message": "hello!"
                    }

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /chat/belligerents/<addressee>``
    Send message in chat to a belligerent (army).

    Parameters
        In URL
            ``addressee``
                Belligerent to chat to. See `il2fb.commons.organization.Belligerents <https://github.com/IL2HorusTeam/il2fb-commons/blob/master/il2fb/commons/organization.py#L20>`_
                for details.

                Type
                    ``integer``

                Example:
                    ``/chat/belligerents/1``

        In body
            ``message``
                Message to send.

                Type
                    ``string``

            Body example
                .. code-block:: json

                    {
                        "message": "hello!"
                    }

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``GET /missions/<path>``
    Browse missions storage (directories, ``.mis`` and ``.properties`` files).

    Parameters
        In URL
            ``path``
                Path to a directory or mission relative to server's
                ``Missions`` directory. ``Missions`` root directory is used if
                ``path`` is not specified.

                Type
                    ``string``

                Example for directory
                    ``/missions/Net/dogfight``

                Example for mission
                    ``/missions/Net/dogfight/demo_sample.mis``

        In query:
            ``json``
                Optional parameter for getting parsed mission instead of raw
                text. Parsing is done by `il2fb-mission-parser <https://github.com/IL2HorusTeam/il2fb-mission-parser>`_
                library.

            Type
                ``string``

            Example
                ``/missions/Net/dogfight/demo_sample.mis?json``

    Responses
        ``200``
            List of files and directories if resource is a directory.

            Example
                .. code-block:: json

                    {
                        "dirs": [
                            "   1",
                            "   2",
                            "   3",
                            "   4",
                            "Pacific Fighters"
                        ],
                        "files": [
                            "demo_sample.mis",
                            "demo_sample_ru.properties"
                        ]
                    }

        ``200``
            Mission content as plain text if resource is a mission.

        ``200``
            Parsed mission content as JSON if resource is a mission and
            ``json`` parameter is specified.
            `Refer to parser's demo page <http://il2horusteam.github.io/il2fb-mission-parser/>`_
            to explore resulting format.

        ``404``
            Requested resource does not exist.

        ``500``
            Mission parsing or another error has occurred.

    Authorization
        Required if configured.


``POST /missions/<path>``
    Upload mission and properties to a given directory in storage.

    Parameters
        In URL
            ``path``
                Path to a directory relative to server's ``Missions``
                directory. ``Missions`` root directory is used if ``path`` is
                not specified.

                Type
                    ``string``

                Example
                    ``/missions/Net/dogfight``

        In body
            Mission and properties are passed as parts of
            ``multipart/form-data`` request. Name of form fields does not
            matter. Amount of files being uploaded is not limited.

            Request body example:
                .. code-block::

                    POST /missions/Net/dogfight/dev HTTP/1.1
                    Host: 127.0.0.1:5000
                    Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

                    ------WebKitFormBoundary7MA4YWxkTrZu0gW
                    Content-Disposition: form-data; name="file"; filename="demo_sample.mis"
                    Content-Type:


                    ------WebKitFormBoundary7MA4YWxkTrZu0gW
                    Content-Disposition: form-data; name="props"; filename="demo_sample_ru.properties"
                    Content-Type:


                    ------WebKitFormBoundary7MA4YWxkTrZu0gW--

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Side effects
        - Target directory is created if it does not exist.
        - Files are overwritten if they are already exist.

    Authorization
        Required if configured.


``DELETE /missions/<path>``
    Delete mission with its property files from storage.

    Parameters
        In URL
            ``path``
                Path to a mission relative to server's ``Missions`` directory.

                Type
                    ``string``

                Example
                    ``/missions/Net/dogfight/demo_sample.mis``

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

        ``404``
            Requested mission does not exist.

    Side effects
        ``.property`` files which are associated with a given mission are also
        deleted if present.

    Authorization
        Required if configured.


``GET /missions/current/info``
    Get information about current mission. Wraps ``mission`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            Serialized `il2fb.ds.middleware.console.structures.MissionInfo <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/console/structures.py#L154>`_
            structure.

            Example
                .. code-block:: json

                    {
                        "status": {
                            "name": "not_loaded"
                        },
                        "file_path": null,
                        "__type__": "il2fb.ds.middleware.console.structures.MissionInfo"
                    }

    Authorization
        Required if configured.


``POST /missions/<path>/load``
    Load a given mission to make it current. Wraps ``mission LOAD`` console
    command.

    Parameters
        In URL
            ``path``
                Path to a mission relative to server's ``Missions`` directory.

                Type
                    ``string``

                Example
                    ``/missions/Net/dogfight/demo_sample.mis/load``

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /missions/current/begin``
    Begin current mission. Wraps ``mission BEGIN`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /missions/current/end``
    End current mission. Wraps ``mission END`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``POST /missions/current/unload``
    Unload current mission. Wraps ``mission DESTROY`` console command.

    Parameters
        No parameters.

    Responses
        ``200``
            Empty dictionary.

            Example
                .. code-block:: json

                    {}

    Authorization
        Required if configured.


``GET /radar/ships``
    Get positions of all ships (moving and stationary).

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.ShipPosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L57>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 0,
                            "id": "0_Chief",
                            "pos": {
                                "x": 8445,
                                "y": 138394
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 1,
                            "id": "1_Chief",
                            "pos": {
                                "x": 37758,
                                "y": 225193
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 2,
                            "id": "8_Chief",
                            "pos": {
                                "x": 29003,
                                "y": 152135
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 3,
                            "id": "70_Static",
                            "pos": {
                                "x": 43387,
                                "y": 154521
                            },
                            "is_stationary": true,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 4,
                            "id": "72_Static",
                            "pos": {
                                "x": 43448,
                                "y": 152697
                            },
                            "is_stationary": true,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        }
                    ]

    Authorization
        Required if configured.


``GET /radar/ships/moving``
    Get positions of moving ships.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.ShipPosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L57>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 0,
                            "id": "0_Chief",
                            "pos": {
                                "x": 8341,
                                "y": 138642
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 1,
                            "id": "1_Chief",
                            "pos": {
                                "x": 37510,
                                "y": 224931
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 2,
                            "id": "8_Chief",
                            "pos": {
                                "x": 28869,
                                "y": 152486
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        }
                    ]

    Authorization
        Required if configured.

``GET /radar/ships/stationary``
    Get positions of stationary ships.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.ShipPosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L57>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 3,
                            "id": "70_Static",
                            "pos": {
                                "x": 43387,
                                "y": 154521
                            },
                            "is_stationary": true,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 4,
                            "id": "72_Static",
                            "pos": {
                                "x": 43448,
                                "y": 152697
                            },
                            "is_stationary": true,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        }
                    ]

    Authorization
        Required if configured.


``GET /radar/aircrafts/moving``
    Get positions of moving aircrafts (controlled by users or AI).

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.MovingAircraftPosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L23>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 0,
                            "id": "I_JG100",
                            "pos": {
                                "x": 80396,
                                "y": 168150,
                                "z": 1511
                            },
                            "is_human": false,
                            "member_index": 0,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        },
                        {
                            "index": 1,
                            "id": "I_JG100",
                            "pos": {
                                "x": 80329,
                                "y": 168158,
                                "z": 1510
                            },
                            "is_human": false,
                            "member_index": 1,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        },
                        {
                            "index": 2,
                            "id": "g0101",
                            "pos": {
                                "x": 66378,
                                "y": 160822,
                                "z": 1512
                            },
                            "is_human": false,
                            "member_index": 0,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        },
                        {
                            "index": 3,
                            "id": "g0101",
                            "pos": {
                                "x": 66307,
                                "y": 160823,
                                "z": 1510
                            },
                            "is_human": false,
                            "member_index": 1,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        },
                        {
                            "index": 4,
                            "id": "john.doe",
                            "pos": {
                                "x": 110695,
                                "y": 202555,
                                "z": 11
                            },
                            "is_human": true,
                            "member_index": null,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        }
                    ]

    Authorization
        Required if configured.


``GET /radar/ground-units/moving``
    Get positions of moving ground units.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L41>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 0,
                            "id": "2_Chief",
                            "member_index": 0,
                            "pos": {
                                "x": 99673,
                                "y": 202473,
                                "z": 43
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                        },
                        {
                            "index": 1,
                            "id": "4_Chief",
                            "member_index": 0,
                            "pos": {
                                "x": 163918,
                                "y": 204481,
                                "z": 15
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                        },
                        {
                            "index": 2,
                            "id": "4_Chief",
                            "member_index": 1,
                            "pos": {
                                "x": 163928,
                                "y": 204471,
                                "z": 14
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                        }
                    ]

    Authorization
        Required if configured.


``GET /radar/moving``
    Get positions of all moving actors (aircrafts, ground units and moving
    ships).

    Parameters
        No parameters.

    Responses
        ``200``
            Serialized structure `il2fb.ds.airbridge.radar.AllMovingActorsPositions <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/radar.py#L24>`_.

            Example
                .. code-block:: json

                    {
                        "aircrafts": [
                            {
                                "index": 0,
                                "id": "I_JG100",
                                "pos": {
                                    "x": 82480,
                                    "y": 161721,
                                    "z": 1861
                                },
                                "is_human": false,
                                "member_index": 0,
                                "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                            },
                            {
                                "index": 1,
                                "id": "john.doe",
                                "pos": {
                                    "x": 110695,
                                    "y": 202554,
                                    "z": 11
                                },
                                "is_human": true,
                                "member_index": null,
                                "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                            }
                        ],
                        "ground_units": [
                            {
                                "index": 0,
                                "id": "2_Chief",
                                "member_index": 0,
                                "pos": {
                                    "x": 99903,
                                    "y": 203297,
                                    "z": 41
                                },
                                "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                            },
                            {
                                "index": 1,
                                "id": "3_Chief",
                                "member_index": 0,
                                "pos": {
                                    "x": 88322,
                                    "y": 184137,
                                    "z": 1
                                },
                                "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                            }
                        ],
                        "ships": [
                            {
                                "index": 0,
                                "id": "0_Chief",
                                "pos": {
                                    "x": 7720,
                                    "y": 140132
                                },
                                "is_stationary": false,
                                "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                            },
                            {
                                "index": 1,
                                "id": "1_Chief",
                                "pos": {
                                    "x": 35568,
                                    "y": 222874
                                },
                                "is_stationary": false,
                                "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                            }
                        ],
                        "__type__": "il2fb.ds.airbridge.radar.AllMovingActorsPositions"
                    }

    Authorization
        Required if configured.


``GET /radar/houses``
    Get positions of houses.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.HousePosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L82>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 0,
                            "id": "0_bld",
                            "pos": {
                                "x": 100184,
                                "y": 167170
                            },
                            "status": {
                                "name": "alive",
                                "value": "A"
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                        },
                        {
                            "index": 1,
                            "id": "1_bld",
                            "pos": {
                                "x": 100174,
                                "y": 167142
                            },
                            "status": {
                                "name": "alive",
                                "value": "A"
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                        }
                    ]

    Authorization
        Required if configured.


``GET /radar/stationary-objects``
    Get positions of stationary objects.

    Parameters
        No parameters.

    Responses
        ``200``
            List of `il2fb.ds.middleware.device_link.structures.StationaryObjectPosition <https://github.com/IL2HorusTeam/il2fb-ds-middleware/blob/master/il2fb/ds/middleware/device_link/structures.py#L73>`_
            structures.

            Example
                .. code-block:: json

                    [
                        {
                            "index": 0,
                            "id": "0_Static",
                            "pos": {
                                "x": 71906,
                                "y": 178119,
                                "z": 1
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                        },
                        {
                            "index": 1,
                            "id": "1_Static",
                            "pos": {
                                "x": 71616,
                                "y": 176956,
                                "z": 1
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                        }
                    ]

    Authorization
        Required if configured.


``GET /radar/stationary``
    Get positions of all stationary actors (stationary objects, houses and
    stationary ships).

    Parameters
        No parameters.

    Responses
        ``200``
            Serialized structure `il2fb.ds.airbridge.radar.AllStationaryActorsPositions <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/radar.py#L38>`_.

            Example
                .. code-block:: json

                    {
                        "stationary_objects": [
                            {
                                "index": 0,
                                "id": "0_Static",
                                "pos": {
                                    "x": 71906,
                                    "y": 178119,
                                    "z": 1
                                },
                                "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                            },
                            {
                                "index": 1,
                                "id": "1_Static",
                                "pos": {
                                    "x": 71616,
                                    "y": 176956,
                                    "z": 1
                                },
                                "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                            }
                        ],
                        "houses": [
                            {
                                "index": 0,
                                "id": "0_bld",
                                "pos": {
                                    "x": 100184,
                                    "y": 167170
                                },
                                "status": {
                                    "name": "alive",
                                    "value": "A"
                                },
                                "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                            },
                            {
                                "index": 1,
                                "id": "1_bld",
                                "pos": {
                                    "x": 100174,
                                    "y": 167142
                                },
                                "status": {
                                    "name": "alive",
                                    "value": "A"
                                },
                                "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                            }
                        ],
                        "ships": [
                            {
                                "index": 3,
                                "id": "70_Static",
                                "pos": {
                                    "x": 43387,
                                    "y": 154521
                                },
                                "is_stationary": true,
                                "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                            },
                            {
                                "index": 4,
                                "id": "72_Static",
                                "pos": {
                                    "x": 43448,
                                    "y": 152697
                                },
                                "is_stationary": true,
                                "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                            }
                        ],
                        "__type__": "il2fb.ds.airbridge.radar.AllStationaryActorsPositions"
                    }

    Authorization
        Required if configured.


NATS
~~~~

Airbridge provides requests API over NATS by using it's
`request-reply <http://nats.io/documentation/concepts/nats-req-rep/>`_
mechanism.

All messages are formatted as JSON just like in case of REST.

Each request message defines its operation by ``opcode`` parameter of
``integer`` type.

Those requests, which accept arguments, specify ``payload`` parameter as
dictionary.

Optional ``timeout`` argument is also available for all requests. As in case
of REST API, this parameter has type ``float`` and is measured in seconds, for
example:

.. code-block:: json

    {
        "opcode": 0,
        "payload": {
            "timeout": 5
        }
    }

Every response contains ``status``. It is an integer representation of request
execution status, where ``0`` stands for success and ``1`` — for failure.
Example:

.. code-block:: json

    {
        "status": 0
    }


Available NATS requests are listed below along with examples of responses.


``GET_SERVER_INFO``
    Get information about server. Wraps ``server`` console command.

    Opcode
        ``0``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 0
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": {
                    "type": "Local server",
                    "name": "Development server",
                    "description": "Dedicated Server for local tests",
                    "__type__": "il2fb.ds.middleware.console.structures.ServerInfo"
                }
            }


``GET_HUMANS_LIST``
    Get list of users connected to server. Wraps ``user`` console command.

    Opcode
        ``10``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 10
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "callsign": "john.doe",
                        "ping": 61,
                        "score": 0,
                        "belligerent": {
                            "name": "none",
                            "value": 0,
                            "verbose_name": "none",
                            "help_text": null,
                        },
                        "aircraft": null,
                        "__type__": "il2fb.ds.middleware.console.structures.Human"
                    }
                ]
            }


``GET_HUMANS_COUNT``
    Get number of users connected to server. Equals to a number of records
    returned by ``user`` console command.

    Opcode
        ``11``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 11
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": 7
            }


``GET_HUMANS_STATISTICS``
    Get server's statistics for users connected to server.
    Wraps ``user STAT`` console command.

    Opcode
        ``12``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 12
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "callsign": "john.doe",
                        "score": 0,
                        "state": "Selects Aircraft",
                        "enemy_aircraft_kills": 0,
                        "enemy_static_aircraft_kills": 0,
                        "enemy_tank_kills": 0,
                        "enemy_car_kills": 0,
                        "enemy_artillery_kills": 0,
                        "enemy_aaa_kills": 0,
                        "enemy_wagon_kills": 0,
                        "enemy_ship_kills": 0,
                        "enemy_radio_kills": 0,
                        "friendly_aircraft_kills": 0,
                        "friendly_static_aircraft_kills": 0,
                        "friendly_tank_kills": 0,
                        "friendly_car_kills": 0,
                        "friendly_artillery_kills": 0,
                        "friendly_aaa_kills": 0,
                        "friendly_wagon_kills": 0,
                        "friendly_ship_kills": 0,
                        "friendly_radio_kills": 0,
                        "bullets_fired": 0,
                        "bullets_hit": 0,
                        "bullets_hit_air_targets": 0,
                        "rockets_launched": 0,
                        "rockets_hit": 0,
                        "bombs_dropped": 0,
                        "bombs_hit": 0,
                        "__type__": "il2fb.ds.middleware.console.structures.HumanStatistics"
                    }
                ]
            }


``KICK_ALL_HUMANS``
    Kick all users from server.

    Opcode
        ``20``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 20
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": 0
            }


``KICK_HUMAN_BY_CALLSIGN``
    Kick user from server by user's callsign.

    Opcode
        ``21``

    Parameters
        ``callsign``
            Callsign of user to kick.

            Type
                ``string``

    Request example
        .. code-block:: json

            {
                "opcode": 21,
                "payload": {
                    "callsign": "john.doe"
                }
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``CHAT_TO_ALL``
    Send message in chat to everyone.

    Opcode
        ``30``

    Parameters
        ``message``
            Message to send.

            Type
                ``string``

    Request example
        .. code-block:: json

            {
                "opcode": 30,
                "payload": {
                    "message": "hello!"
                }
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``CHAT_TO_HUMAN``
    Send message in chat to a user.

    Opcode
        ``31``

    Parameters
        ``message``
            Message to send.

            Type
                ``string``

        ``addressee``
            Callsign of user to chat to.

            Type
                ``string``

    Request example
        .. code-block:: json

            {
                "opcode": 31,
                "payload": {
                    "message": "hello!",
                    "addressee": "john.doe"
                }
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``CHAT_TO_BELLIGERENT``
    Send message in chat to a belligerent (army).

    Opcode
        ``32``

    Parameters
        ``message``
            Message to send.

            Type
                ``string``

        ``addressee``
            Callsign of belligerent to chat to. See `il2fb.commons.organization.Belligerents <https://github.com/IL2HorusTeam/il2fb-commons/blob/master/il2fb/commons/organization.py#L20>`_
            for details.

            Type
                ``integer``

    Request example
        .. code-block:: json

            {
                "opcode": 32,
                "payload": {
                    "message": "hello!",
                    "addressee": 1
                }
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``GET_MISSION_INFO``
    Get information about current mission. Wraps ``mission`` console command.

    Opcode
        ``40``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 40
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": {
                    "status": {
                        "name": "not_loaded"
                    },
                    "file_path": null,
                    "__type__": "il2fb.ds.middleware.console.structures.MissionInfo"
                }
            }


``LOAD_MISSION``
    Load a given mission to make it current. Wraps ``mission LOAD`` console
    command.

    Opcode
        ``41``

    Parameters
        ``file_path``
            Path to a mission relative to server's ``Missions`` directory.

            Type
                ``string``

    Request example
        .. code-block:: json

            {
                "opcode": 41,
                "payload": {
                    "file_path": "Net/dogfight/demo_sample.mis"
                }
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``BEGIN_MISSION``
    Begin current mission. Wraps ``mission BEGIN`` console command.

    Opcode
        ``42``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 42
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``END_MISSION``
    End current mission. Wraps ``mission END`` console command.

    Opcode
        ``43``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 43
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``UNLOAD_MISSION``
    Unload current mission. Wraps ``mission DESTROY`` console command.

    Opcode
        ``44``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 44
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": null
            }


``GET_ALL_SHIPS_POSITIONS``
    Get positions of all ships (moving and stationary).

    Opcode
        ``50``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 50
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 0,
                        "id": "0_Chief",
                        "pos": {
                            "x": 8445,
                            "y": 138394
                        },
                        "is_stationary": false,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 1,
                        "id": "1_Chief",
                        "pos": {
                            "x": 37758,
                            "y": 225193
                        },
                        "is_stationary": false,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 2,
                        "id": "8_Chief",
                        "pos": {
                            "x": 29003,
                            "y": 152135
                        },
                        "is_stationary": false,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 3,
                        "id": "70_Static",
                        "pos": {
                            "x": 43387,
                            "y": 154521
                        },
                        "is_stationary": true,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 4,
                        "id": "72_Static",
                        "pos": {
                            "x": 43448,
                            "y": 152697
                        },
                        "is_stationary": true,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    }
                ]
            }


``GET_MOVING_SHIPS_POSITIONS``
    Get positions of moving ships.

    Opcode
        ``51``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 51
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 0,
                        "id": "0_Chief",
                        "pos": {
                            "x": 8445,
                            "y": 138394
                        },
                        "is_stationary": false,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 1,
                        "id": "1_Chief",
                        "pos": {
                            "x": 37758,
                            "y": 225193
                        },
                        "is_stationary": false,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 2,
                        "id": "8_Chief",
                        "pos": {
                            "x": 29003,
                            "y": 152135
                        },
                        "is_stationary": false,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    }
                ]
            }


``GET_STATIONARY_SHIPS_POSITIONS``
    Get positions of stationary ships.

    Opcode
        ``52``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 52
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 3,
                        "id": "70_Static",
                        "pos": {
                            "x": 43387,
                            "y": 154521
                        },
                        "is_stationary": true,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    },
                    {
                        "index": 4,
                        "id": "72_Static",
                        "pos": {
                            "x": 43448,
                            "y": 152697
                        },
                        "is_stationary": true,
                        "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                    }
                ]
            }


``GET_MOVING_AIRCRAFTS_POSITIONS``
    Get positions of moving aircrafts (controlled by users or AI).

    Opcode
        ``53``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 53
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 0,
                        "id": "I_JG100",
                        "pos": {
                            "x": 80396,
                            "y": 168150,
                            "z": 1511
                        },
                        "is_human": false,
                        "member_index": 0,
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                    },
                    {
                        "index": 1,
                        "id": "I_JG100",
                        "pos": {
                            "x": 80329,
                            "y": 168158,
                            "z": 1510
                        },
                        "is_human": false,
                        "member_index": 1,
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                    },
                    {
                        "index": 2,
                        "id": "g0101",
                        "pos": {
                            "x": 66378,
                            "y": 160822,
                            "z": 1512
                        },
                        "is_human": false,
                        "member_index": 0,
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                    },
                    {
                        "index": 3,
                        "id": "g0101",
                        "pos": {
                            "x": 66307,
                            "y": 160823,
                            "z": 1510
                        },
                        "is_human": false,
                        "member_index": 1,
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                    },
                    {
                        "index": 4,
                        "id": "john.doe",
                        "pos": {
                            "x": 110695,
                            "y": 202555,
                            "z": 11
                        },
                        "is_human": true,
                        "member_index": null,
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                    }
                ]
            }


``GET_MOVING_GROUND_UNITS_POSITIONS``
    Get positions of moving ground units.

    Opcode
        ``54``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 54
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 0,
                        "id": "2_Chief",
                        "member_index": 0,
                        "pos": {
                            "x": 99673,
                            "y": 202473,
                            "z": 43
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                    },
                    {
                        "index": 1,
                        "id": "4_Chief",
                        "member_index": 0,
                        "pos": {
                            "x": 163918,
                            "y": 204481,
                            "z": 15
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                    },
                    {
                        "index": 2,
                        "id": "4_Chief",
                        "member_index": 1,
                        "pos": {
                            "x": 163928,
                            "y": 204471,
                            "z": 14
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                    }
                ]
            }


``GET_ALL_MOVING_ACTORS_POSITIONS``
    Get positions of all moving actors (aircrafts, ground units and moving
    ships).

    Opcode
        ``55``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 55
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": {
                    "aircrafts": [
                        {
                            "index": 0,
                            "id": "I_JG100",
                            "pos": {
                                "x": 82480,
                                "y": 161721,
                                "z": 1861
                            },
                            "is_human": false,
                            "member_index": 0,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        },
                        {
                            "index": 1,
                            "id": "john.doe",
                            "pos": {
                                "x": 110695,
                                "y": 202554,
                                "z": 11
                            },
                            "is_human": true,
                            "member_index": null,
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                        }
                    ],
                    "ground_units": [
                        {
                            "index": 0,
                            "id": "2_Chief",
                            "member_index": 0,
                            "pos": {
                                "x": 99903,
                                "y": 203297,
                                "z": 41
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                        },
                        {
                            "index": 1,
                            "id": "3_Chief",
                            "member_index": 0,
                            "pos": {
                                "x": 88322,
                                "y": 184137,
                                "z": 1
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                        }
                    ],
                    "ships": [
                        {
                            "index": 0,
                            "id": "0_Chief",
                            "pos": {
                                "x": 7720,
                                "y": 140132
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 1,
                            "id": "1_Chief",
                            "pos": {
                                "x": 35568,
                                "y": 222874
                            },
                            "is_stationary": false,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        }
                    ],
                    "__type__": "il2fb.ds.airbridge.radar.AllMovingActorsPositions"
                }
            }


``GET_ALL_HOUSES_POSITIONS``
    Get positions of houses.

    Opcode
        ``56``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 56
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 0,
                        "id": "0_bld",
                        "pos": {
                            "x": 100184,
                            "y": 167170
                        },
                        "status": {
                            "name": "alive",
                            "value": "A"
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                    },
                    {
                        "index": 1,
                        "id": "1_bld",
                        "pos": {
                            "x": 100174,
                            "y": 167142
                        },
                        "status": {
                            "name": "alive",
                            "value": "A"
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                    }
                ]
            }


``GET_STATIONARY_OBJECTS_POSITIONS``
    Get positions of stationary objects.

    Opcode
        ``57``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 57
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": [
                    {
                        "index": 0,
                        "id": "0_Static",
                        "pos": {
                            "x": 71906,
                            "y": 178119,
                            "z": 1
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                    },
                    {
                        "index": 1,
                        "id": "1_Static",
                        "pos": {
                            "x": 71616,
                            "y": 176956,
                            "z": 1
                        },
                        "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                    }
                ]
            }


``GET_ALL_STATIONARY_ACTORS_POSITIONS``
    Get positions of all stationary actors (stationary objects, houses and
    stationary ships).

    Opcode
        ``58``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 58
            }

    Response example:
        .. code-block:: json

            {
                "status": 0,
                "payload": {
                    "stationary_objects": [
                        {
                            "index": 0,
                            "id": "0_Static",
                            "pos": {
                                "x": 71906,
                                "y": 178119,
                                "z": 1
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                        },
                        {
                            "index": 1,
                            "id": "1_Static",
                            "pos": {
                                "x": 71616,
                                "y": 176956,
                                "z": 1
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.StationaryObjectPosition"
                        }
                    ],
                    "houses": [
                        {
                            "index": 0,
                            "id": "0_bld",
                            "pos": {
                                "x": 100184,
                                "y": 167170
                            },
                            "status": {
                                "name": "alive",
                                "value": "A"
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                        },
                        {
                            "index": 1,
                            "id": "1_bld",
                            "pos": {
                                "x": 100174,
                                "y": 167142
                            },
                            "status": {
                                "name": "alive",
                                "value": "A"
                            },
                            "__type__": "il2fb.ds.middleware.device_link.structures.HousePosition"
                        }
                    ],
                    "ships": [
                        {
                            "index": 3,
                            "id": "70_Static",
                            "pos": {
                                "x": 43387,
                                "y": 154521
                            },
                            "is_stationary": true,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        },
                        {
                            "index": 4,
                            "id": "72_Static",
                            "pos": {
                                "x": 43448,
                                "y": 152697
                            },
                            "is_stationary": true,
                            "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                        }
                    ],
                    "__type__": "il2fb.ds.airbridge.radar.AllStationaryActorsPositions"
                }
            }


Streaming
---------

As it was stated earlier, Airbridge provides multiple streaming facilities.
This means that it's possible to subscribe to a stream of events which
originate from different sources. The following sources are provided:

#. ``chat`` — messages coming from chat. This includes messages from server and
   system.
#. ``events`` — events coming from game log and user-connection events coming
   from server's console;
#. ``not parsed strings`` — strings coming from game log which were not parsed
   due some error;
#. ``radar`` — coordinates of all moving actors which are queried periodically
   and period is specified for each subscriber separatelly. Default refresh
   period is ``5 sec``.

Streaming facilities allow subscription of any object which conforms to
`StreamingSubscriber <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/streaming/subscribers/base.py#L8>`_
interface.

Those subscribers which conform to `PluggableStreamingSubscriber <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/streaming/subscribers/base.py#L15>`_
interface, can be created automatically at startup of application.
`TextFileStreamingSink <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/streaming/subscribers/file.py#L11>`_,
`JSONFileStreamingSink <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/streaming/subscribers/file.py#L51>`_
and `NATSStreamingSink <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/il2fb/ds/airbridge/streaming/subscribers/nats.py#L17>`_
are examples of pluggable subscribers. Configuration of such subscribers is
explained in "Configuration" section.

All streaming data is transmitted as message which are formatted as JSON
strings. Each message contains a ``timestamp`` which indicates time when event
was detected and ``data`` which contains event-related data.

..

    **NOTE**: event's timestamp indicates time when event was detected, not
    the time when it has occured. Usually these times are equal, but there may
    be a slight difference, for example, for game log events: game log is
    monitored by polling file with a specific period and events may occur
    before log watcher will notice them. Moreover, game server may write
    messages to game log with delay. So, it's better to extract event's time
    from event's data if it is present and to use ``timestamp`` field as event
    identifier.

Examples of messages from different streaming facilities are given below.

Message from ``chat`` stream:

.. code-block:: json

    {
        "timestamp": "2017-11-25T13:22:42.145599",
        "data": {
            "body": "john.doe joins the game.",
            "actor": null,
            "from_human": false,
            "from_server": false,
            "from_system": true,
            "__type__": "il2fb.ds.middleware.console.events.ChatMessageWasReceived"
        }
    }

Message from ``events`` stream:

.. code-block:: json

    {
        "timestamp": "2017-11-25T15:22:45.211668",
        "data": {
            "time": "15:22:44",
            "actor": {
                "flight": "g0101",
                "aircraft": 3
            },
            "pos": {
                "x": 55079.348,
                "y": 175689.23
            },
            "__type__": "il2fb.parsers.game_log.events.AIAircraftHasDespawned"
        }
    }

Message from ``not parsed strings`` stream:

.. code-block:: json

    {
        "timestamp": "2017-11-25T15:19:33.754441",
        "data": {
            "value": "[3:19:33 PM] 3do/Tree/Line/live.sim destroyed by 8_Chief at 69716.7 158365.38",
            "__type__": "il2fb.ds.airbridge.dedicated_server.game_log.NotParsedGameLogString"
        }
    }

Message from ``radar`` stream:

.. code-block:: json

    {
        "timestamp": "2017-11-25T15:50:51.689771",
        "data": {
            "aircrafts": [
                {
                    "index": 0,
                    "id": "I_JG100",
                    "pos": {
                        "x": 82480,
                        "y": 161721,
                        "z": 1861
                    },
                    "is_human": false,
                    "member_index": 0,
                    "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                },
                {
                    "index": 1,
                    "id": "john.doe",
                    "pos": {
                        "x": 110695,
                        "y": 202554,
                        "z": 11
                    },
                    "is_human": true,
                    "member_index": null,
                    "__type__": "il2fb.ds.middleware.device_link.structures.MovingAircraftPosition"
                }
            ],
            "ground_units": [
                {
                    "index": 0,
                    "id": "2_Chief",
                    "member_index": 0,
                    "pos": {
                        "x": 99903,
                        "y": 203297,
                        "z": 41
                    },
                    "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                },
                {
                    "index": 1,
                    "id": "3_Chief",
                    "member_index": 0,
                    "pos": {
                        "x": 88322,
                        "y": 184137,
                        "z": 1
                    },
                    "__type__": "il2fb.ds.middleware.device_link.structures.MovingGroundUnitPosition"
                }
            ],
            "ships": [
                {
                    "index": 0,
                    "id": "0_Chief",
                    "pos": {
                        "x": 7720,
                        "y": 140132
                    },
                    "is_stationary": false,
                    "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                },
                {
                    "index": 1,
                    "id": "1_Chief",
                    "pos": {
                        "x": 35568,
                        "y": 222874
                    },
                    "is_stationary": false,
                    "__type__": "il2fb.ds.middleware.device_link.structures.ShipPosition"
                }
            ],
            "__type__": "il2fb.ds.airbridge.radar.AllMovingActorsPositions"
        }
    }

The subsections below describe different subscribers which can be used as
streaming destination.


Files
~~~~~

Airbridge supports streaming of data to local files. In this case every single
line in text file will contain a message serialized as a single JSON string.

This is the simplest and the fastest streaming subscriber, however it is
limited to local file system of server.

Events from different streaming facilities must go to different output files.

Streaming to files can be configured to run from start of application.

Refer to "Configuration" section for examples and details.


NATS
~~~~

Streaming to NATS channels allows Airbridge to send data to remote storage.

This is one of the key functionalities of Airbridge, as it allows to escape
server's file system and operating system at all. This also makes it possible
for multiple remote consumers to subscribe to events in different combinations.

Also NATS streaming server allows to configure persistence of messages, so they
can be accessed and processed in future.

Each streaming facility can publish messages to its own channel (subject).
Publishing all messages to a single channel is also possible if needed.

Streaming to NATS channels can be configured to run from start of application.

Refer to "Configuration" section for examples and details.


WebSockets
~~~~~~~~~~

Airbridge allows its clients to subscribe to streaming facilities via
WebSockets.

This means that web application can show data in real time in browser. Such
feature can be used for building admin dashboards for Airbridge. It's not
recommended to use this API for displaying data to end users in production, as
this can affect overall performance of Airbridge.

To start any subscription, a client must connect to streaming endpoint via
web-socket. This is done by sending ``HTTP GET`` request to ``/streaming``
route, e.g.:

::

    GET ws://127.0.0.1:5000/streaming

After connection is established, the client can send messages to server to
subscribe to or unsubscribe from a specific streaming facility.

Like in case of NATS requests API, each request to WS streaming subscription
API is specified by operation code ``opcode``. Responses have similar structure
as well: every response contains integer ``status`` field, where ``0`` stands
for success and ``1`` — for failure.

Subscription requests are described below.


``SUBSCRIBE_TO_CHAT``
    Subscribe to ``chat`` stream.

    Opcode
        ``0``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 0
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``UNSUBSCRIBE_FROM_CHAT``
    Unsubscribe from ``chat`` stream.

    Opcode
        ``1``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 1
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``SUBSCRIBE_TO_EVENTS``
    Subscribe to ``events`` stream.

    Opcode
        ``10``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 10
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``UNSUBSCRIBE_FROM_EVENTS``
    Unsubscribe from ``events`` stream.

    Opcode
        ``11``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 11
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``SUBSCRIBE_TO_NOT_PARSED_STRINGS``
    Subscribe to ``not parsed strings`` stream.

    Opcode
        ``20``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 20
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``UNSUBSCRIBE_FROM_NOT_PARSED_STRINGS``
    Unsubscribe from ``not parsed strings`` stream.

    Opcode
        ``21``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 21
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``SUBSCRIBE_TO_RADAR``
    Subscribe to ``radar`` stream.

    Opcode
        ``30``

    Parameters
        ``refresh_period``
            Refresh period of radar for current subscriber. Measured in
            seconds. The parameter is optional.

            Type
                ``float``

    Request example
        .. code-block:: json

            {
                "opcode": 30,
                "payload": {
                    "refresh_period": 30
                }
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


``UNSUBSCRIBE_FROM_RADAR``
    Unsubscribe from ``radar`` stream.

    Opcode
        ``31``

    Parameters
        No parameters.

    Request example
        .. code-block:: json

            {
                "opcode": 31
            }

    Response example:
        .. code-block:: json

            {
                "status": 0
            }


Releases
========

Information about project's releases can be found at
`releases page <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/releases>`_.

Each release includes release notes, precompiled binaries and sources.


Installation
============

This section describes possible ways to install Airbridge application.
The easiest way is to install from binary which is described below.


From binary
-----------

Airbridge comes with precompiled executable binaries which are available at
releases page (see the section above). Installation is simple and it is done
just by unpacking executable file from release archive which is suitable for
target operating system.


From PyPI
---------

It's also possible to get Airbridge as Python package from PyPI
(Python Package Index). It is available as `il2fb-ds-airbridge <https://pypi.python.org/pypi?name=il2fb-ds-airbridge&:action=display>`_
package and can be installed via ``pip``:

.. code-block:: bash

    pip install il2fb-ds-airbridge

Same via ``easy_install``:

.. code-block:: bash

    easy_install il2fb-ds-airbridge

..

    **NOTE**: Airbridge is implemented using Python 3.6, so at least this
    version must be used to run the application.


From sources
------------

If neither precompiled version nor package are suitable or
debugging/development is needed, then Airbridge can be installed from local
sources.

Sources can be obtained by cloning Git repository or by downloading them from
releases page.

Usual installation can be done by executing setup script:

.. code-block:: bash

    python ./setup.py install

It is also possible to install application as editable package, so that changes
in source code will be applied immediately:

.. code-block:: bash

    pip install -e .


Manual compilation
------------------

To compile binary from source one will need to use `PyInstaller <http://www.pyinstaller.org>`_.

Its ``spec`` file is defined as ``airbridge.spec`` at the root of source
directory. This makes compilation to be very simple:

.. code-block:: bash

    pyinstaller airbridge.spec -y --clean

PyInstaller will create a binary executable inside ``dist`` directory.

..

    **NOTE**: all dependencies must be installed locally to make it possible to
    compile a single binary file. Dependencies for Windows are defined at
    ``requirements/dist-windows.txt`` and dependencies for other platforms are
    defined at ``requirements/dist.txt``.


Configuration
=============

This section describes how Airbridge can be configured.

Airbridge application requires a configuration file to operate. This
requirement comes out of application's nature: it is a wrapper of dedicated
server, so it needs to know at least were server's executable file is located.

Application's configuration has hierarchical structure and is stored as a YAML
file. The following subsections describe different aspects of configuration.

Full example of configuration file `can be found in examples directory <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/tree/master/examples>`_.


Logging
-------

Logging is critical for detection and localization of issues and errors. As
errors can occur at any stage of application execution, it is important to
configure it in the first place.

Airbridge produces 2 log files: a main log file which records application's
execution flow and a separate file for dumping tracebacks of exceptions.

Let's take a look at configuration of logging which is used by default:

.. code-block:: yaml

    logging:
      files:
        main:
          level: debug
          file_path: airbridge.log
          keep_after_restart: yes
          is_delayed: no
        exceptions:
          file_path: airbridge.exc
          keep_after_restart: yes
          is_delayed: no
      rotation:
          is_enabled: yes
          max_size: 10485760
          max_backups: 10
      trace: no
      encoding: utf8
      use_local_time: no


Files
~~~~~

``files`` section defines options for two log files. The options are the same
for both of them, except ``level`` option which can be specified only for
``main`` file. Description of all options is given below.

``level``
    Logging level for ``main`` file. Can be one of: ``debug``, ``info``,
    ``warning``, ``error`` or ``critical``.

    Logging level for ``exceptions`` file is always set to ``debug``, so that
    tracebacks from any level can be captured. Usually tracebacks are logged
    with log message of ``error`` level, however they are not limited to it.
    For example, warning messages also can include tracebacks.

``file_path``
    Path to a file where log will be stored.

``keep_after_restart``
    Tells whether existing log file should be retained after restart of
    application or a clean one should be created.

``is_delayed``
    Tells whether file should be created only after a first message is written
    to it or it should be created immediately after start of application.


Rotation
~~~~~~~~

Rotation of log files allows to keep their size under acceptable limit. After
file size reaches this limit it is backed up and new empty log file is created.

By default rotation is enabled and size limit for a single file is set to
10'485'760 bytes (10 MiB). This feature can be disabled and external tools
like `logrotate <https://linux.die.net/man/8/logrotate>`_ can be used instead.

``is_enabled``
    Tells whether rotation is turned on.

``max_size``
    Size limit for a single file.

``max_backups``
    Number of backups which are stored in file system before application will
    start to delete old backups. For example, if ``max_backups`` is set to 10
    and there are already 10 backups exist, then when file size of log reaches
    its ``max_size`` limit, the oldest existing backup will be erased and a new
    one will be created.


Other options
~~~~~~~~~~~~~

Other available logging options are listed below.

``trace``
    Tells whether tracing level of logging is enabled. Tracing messages are
    logged with ``debug`` level usually (but not limited to it), so it must be
    set as value for ``level`` option for main log file.

``encoding``
    Encoding of log files to use.

``use_local_time``
    Tells whether local timezone or UTC should be used in log messages.


Daemonization
-------------

By default Airbridge connects its terminal channels (STDIN, STDOUT and STDERR)
to terminal channels channels of dedicated server as it is shown in
"Architecture Overview" section. Such approach allows Airbridge to sit in the
middle of user-server communication and filter data.

If application is going to be run as a background service or inside a
virtualization container like Docker and interactive communication with server
is not needed then it can be turned off by setting ``daemon`` option to ``yes``
value.

``daemon``
    Tells whether Airbridge will be running without ability of user to interact
    with server via its shell: no input prompt and no output.


Example of config with default value:

.. code-block:: yaml

    daemon: no


State persistence
-----------------

Airbridge is designed with ability of its components to store their internal
state so that it can be restored back during next run. For example, monitor of
game log needs to know where it was stopped so that monitoring can be resumed
from the right place to avoid duplication or omission of game events.

State is stored as a file in YAML format, so it can be easily inspected by
humans. Its location is configurable and default configuration is presented
below.

.. code-block:: yaml

    state:
      file_path: airbridge.state

Current configuration is very simple and its options are described below.

``file_path``
    Path to a file where application's state will be stored.


Dedicated server
----------------

This section decribes config options which are used to locate and run an
instance of dedicated server.

Default configuration looks as following:

.. code-block:: yaml

    ds:
      exe_path: C:\\il2ds\il2server.exe
      config_path:
      start_script_path:
      wine_bin_path: wine
      console_proxy:
        bind:
          address: localhost
          port: 20001
      device_link_proxy:
        bind:
          address: localhost
          port: 10001


Description of options is given below.


Primary options
~~~~~~~~~~~~~~~

``exe_path``
    Path to ``il2server.exe`` executable file.

``config_path``
    Optional path to server's config. By default it is ``confs.ini`` which is
    located at server's root directory.

``start_script_path``
    Optional path to server's start script. By default it is ``server.cmd`` which is
    located at server's root directory.

``wine_bin_path``
    Custom path to `Wine <https://www.winehq.org>`_ executable. Applicable only
    when running server on Linux or Mac OS.

    ..

        **NOTE**: on Mac OS ``wine`` executable can be just a shell script
        which wraps invocation of real executable. For example

        .. code-block:: bash

            /usr/local/bin/wine

        can be just a wrapper around

        .. code-block:: bash

            /usr/local/Cellar/wine/1.6.2/bin/wine.bin

        In such case the latter one must be used as value of ``wine_bin_path``.


Console proxy
~~~~~~~~~~~~~

As it was told earlier, console proxy allows existing applications to
communicate with dedicated server using their existing implementations of
console clients.

By default it is turned off.

``console_proxy.bind.address``
    Address for console proxy to listen for incoming connections on.

``console_proxy.bind.port``
    Port for console proxy to listen for incoming connections on.


Device Link proxy
~~~~~~~~~~~~~~~~~

Just like in case of console proxy, Device Link allows existing applications to
communicate with dedicated server using their existing implementations of
Device Link clients.

..

    **NOTE**: Despite Device Link works on top of UDP and dedicated server is
    able to handle requests from multiple clients, it's strongly recommended
    for them to use proxy, as proxy allows multiplexing of requests and
    controls their execution flow.

By default Device Link proxy is turned off.

``device_link_proxy.bind.address``
    Address for Device Link proxy to listen for incoming connections on.

``device_link_proxy.bind.port``
    Port for Device Link proxy to listen for incoming connections on.


NATS
----

As NATS can be used for both API and streaming, it has own configuration
section.

By default NATS API and streaming are turned off, so this section should be
configured only if at least one of them is going to be used.

Full example of configuration:

.. code-block:: yaml

    nats:
      servers:
        - nats://your.domain:4222
      streaming:
        cluster_id: your-cluster-id
        client_id: your-client-id


Description of shown options is given below.

``servers``
    List of server addresses to connect to.
    `See NATS client's documentation <https://github.com/nats-io/asyncio-nats#clustered-usage>`_
    for details.

    Required if either NATS API or streaming is going to be used.

``streaming.cluster_id``
    ID of cluster to connect to. Cluster ID is defined at NATS server side.
    `See streaming server's documentation <https://github.com/nats-io/nats-streaming-server#clustering>`_
    for details.

    Required only if NATS streaming is going to be used.

``streaming.client_id``
    Unique client ID for a given cluster. It is defined by Airbridge user
    usually. `See streaming server's documentation <https://github.com/nats-io/nats-streaming-server#client-connections>`_
    for details.

    Required only if NATS streaming is going to be used.


API
---

API section is used to configure NATS and HTTP APIs. By default APIs are turned
off.

Full example of configuration looks as following:

.. code-block:: yaml

    api:
      nats:
        subject: airbridge-cmd
      http:
        bind:
          address: localhost
          port: 5000
        auth:
          token_header_name: X-Airbridge-Token
          token_storage_path: airbridge.tokens
        cors:
          "your.trusted.domain":
            expose_headers:
              - X-Custom-Server-Header
            allow_headers:
              - X-Requested-With
              - Content-Type
            max_age: 600


NATS
~~~~

It's enough to configure ``nats.servers`` and ``api.nats.subject`` to enable
NATS API. This will tell Airbridge to subscribe to a given subject on a given
set of servers to listen for incoming requests.


HTTP
~~~~

HTTP API includes both REST API and streaming via WebSockets. This subsection
describes configuration options for them.

Minimal configuration requires ``http.bind.port`` option to be specified to
enable HTTP API.


Binding
"""""""

Airbridge must be bound to a specific network location to allow clients to
connect to it.

``http.bind.address``
    Address to listen for incoming HTTP requests on.

    Default value is ``localhost``.

``http.bind.port``
    Post to listen for incoming HTTP requests on.


Authorization options
"""""""""""""""""""""

It's possibe to enable authorization for HTTP requests. This is done by
requiring client to provide an API token which is known only to server and
client. Tokens are passed to Airbridge via HTTP headers.

API tokens are just strings which are encoded with
`base64 algorithm <https://docs.python.org/3/library/base64.html>`_. They
can contain any information and it's OK to use random data. Decision on length
of tokens is up to server administrator.

Encoding to ``base64`` can be done, for example, by
`base64 <https://linux.die.net/man/1/base64>`_ utility, or by running
``openssl enc -base64`` command, or by using Python's
`base64.b64encode() <https://docs.python.org/3/library/base64.html#base64.b64encode>`_
function.

It's possible to generate random and encoded token just by using output from
``/dev/urandom`` device with ``base64`` utility. For example:

.. code-block:: bash

    cat /dev/urandom | head -c 48 | base64

This will produce a random encoded token with length of 48 characters.

Options below describe how to configure authorization via tokens.

``http.auth.token_header_name``
    Name of HTTP header to look for token at.

    Default value is ``X-Airbridge-Token``.

``http.auth.token_storage_path``
    Path to a text file with allowed tokens. Each line represents a single
    token. Multiple tokens can be allowed.


CORS options
""""""""""""

Cross Origin Resource Sharing can be enabled for HTTP API if needed.
Implementation is provided by `aiohttp-cors library <https://github.com/aio-libs/aiohttp-cors>`_.
Options from ``http.cors`` config section are passed to that library as-is.
Please, refer to `library's documentation <https://github.com/aio-libs/aiohttp-cors#usage>`_
for more information.


Streaming
---------

It's possible to configure static streaming subscribers for each streaming
facility separately. By default no subscribers are defined.

All streaming facilities expect ``subscribers`` to be defined for them. Some
facilities like ``radar`` may allow definition of extra options for the whole
facility (e.g., ``request_timeout``).

``subscribers`` option defines a dictionary of subscribers of different types.
Each type of subscribers can accept its own set of arguments for
initialization. This includes, for example, path to output file or name of
a NATS channel. Such initialization options are defined by ``args`` dictionary
which is specific for each subscriber.

Additionally, each subscriber can define additional subscription options for
different facilities. For example, subscribers of ``radar`` facility may
specify custom ``refresh_period``. Such options are defined via
``subscription_options`` parameter.

The configuration example below shows all options which can be used to
configure streaming subscribers.

..

    **NOTE**: it is not necessary to define all kinds of subscribers: it may be
    enough to define only few of them depending on the needs. Other definitions
    `can be found in examples directory <https://github.com/IL2HorusTeam/il2fb-ds-airbridge/tree/master/examples>`_.

.. code-block:: yaml

    streaming:
      chat:
        subscribers:
          file:
            args:
              path: streaming/chat.log
          nats:
            args:
              subject: chat
      events:
        subscribers:
          file:
            args:
              path: streaming/events.log
          nats:
            args:
              subject: events
      not_parsed_strings:
        subscribers:
          file:
            args:
              path: streaming/not_parsed_strings.log
          nats:
            args:
              subject: not-parsed-strings
      radar:
        request_timeout: 5
        subscribers:
          file:
            args:
              path: streaming/radar.log
            subscription_options:
              refresh_period: 5
          nats:
            args:
              subject: radar
            subscription_options:
              refresh_period: 5


Subscribers
~~~~~~~~~~~

Description of subscriber types with their initialization arguments is given
below.


``file``
    File subscriber which puts messages to JSON text file, 1 line per single
    message.

    Args:

    ``path``
        Path to output file.


``nats``
    NATS subscriber which publishes messages to NATS subject (channel).

    Args:

    ``subject``
        Name of NATS subject to publish messages to.


Facilities
~~~~~~~~~~

``chat``, ``events`` and ``not_parsed_strings`` facilities are similar from
configurational point of view and do not have extra options.

On the other hand, ``radar`` facility accepts ``request_timeout`` option which
sets timeout in seconds for Device Link requests. By default there is no
timeout. Additionally, ``radar`` allows to set custom ``refresh_period`` in
seconds for each subscriber via ``subscription_options`` parameter.


Security considerations
=======================

// TODO:


Usage
=====

// TODO:


Caveats
=======

// TODO:


FAQ
===

// TODO:


.. |pypi_package| image:: http://img.shields.io/pypi/v/il2fb-ds-airbridge.svg?style=flat
   :target: https://pypi.python.org/pypi?name=il2fb-ds-airbridge&:action=display

.. |python_versions| image:: https://img.shields.io/badge/Python-3.6-brightgreen.svg?style=flat
   :alt: Supported versions of Python

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat
   :target: https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/LICENSE
   :alt: MIT license

.. |maintainability| image:: https://api.codeclimate.com/v1/badges/d982cd8ce230daba52af/maintainability
   :target: https://codeclimate.com/github/IL2HorusTeam/il2fb-ds-airbridge/maintainability
   :alt: Maintainability provided by «Code Climate»

.. |codebeat| image:: https://codebeat.co/badges/82cf3629-2f6b-4a96-8585-c8241455b8e3
   :target: https://codebeat.co/projects/github-com-il2horusteam-il2fb-ds-airbridge-master
   :alt: Code quality provided by «Codebeat»

.. |codacy| image:: https://api.codacy.com/project/badge/Grade/06e99f9bd40b43d8b95565a900654578?branch=master
   :target: https://www.codacy.com/app/oblalex/il2fb-ds-airbridge
   :alt: Code quality provided by «Codacy»

.. |scrutinizer| image:: https://scrutinizer-ci.com/g/IL2HorusTeam/il2fb-ds-airbridge/badges/quality-score.png?b=master&style=flat
   :target: https://scrutinizer-ci.com/g/IL2HorusTeam/il2fb-ds-airbridge/?branch=master
   :alt: Code quality provided by «Scrutinizer CI»

.. |logo| image:: ./docs/Logo.png
   :alt: Logo
