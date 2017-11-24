IL-2 FB Dedicated Server Airbridge
##################################

|python_versions| |license| |code_climate| |codebeat| |codacy| |scrutinizer|

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


REST
~~~~

The following part of documentation lists and describes REST API endpoints
which are available over HTTP.

Bodies of POST requests and responses of all requests are formatted as JSON.

All endpoints accept optional ``pretty`` query parameter. For example:
``/health?pretty``. It tells endpoints to make "pretty" output by adding
indents. This can be useful for debugging.

Timeouts are passed as query parameters also, e.g.: ``/info?timeout=3``

``GET /health``
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


``POST /chat/humans/<callsign>``
    Send message in chat to a user.

    Parameters
        In URL
            ``callsign``
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


``POST /chat/belligerents/<belligerent>``
    Send message in chat to a belligerent (army).

    Parameters
        In URL
            ``belligerent``
                Callsign of belligerent to chat to. See `il2fb.commons.organization.Belligerents <https://github.com/IL2HorusTeam/il2fb-commons/blob/master/il2fb/commons/organization.py#L20>`_
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

// TODO:


Streaming
---------

// TODO:


WebSockets
~~~~~~~~~~

// TODO:


NATS
~~~~

// TODO:


Installation
============

// TODO:


Configuration
=============

// TODO:


Security
========

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


Development
===========

// TODO:


Changelog
=========


// TODO:


.. |python_versions| image:: https://img.shields.io/badge/Python-3.6-brightgreen.svg?style=flat
   :alt: Supported versions of Python

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat
   :target: https://github.com/IL2HorusTeam/il2fb-ds-airbridge/blob/master/LICENSE
   :alt: MIT license

.. |code_climate| image:: https://codeclimate.com/github/IL2HorusTeam/il2fb-ds-airbridge/badges/gpa.svg
   :target: https://codeclimate.com/github/IL2HorusTeam/il2fb-ds-airbridge
   :alt: Code quality provided by «Code Climate»

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
