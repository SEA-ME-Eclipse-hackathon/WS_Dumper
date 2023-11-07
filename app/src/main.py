# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""A sample skeleton vehicle app."""

import asyncio
import json
import logging
import os
import shutil
import signal

from velocitas_sdk.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from velocitas_sdk.vehicle_app import VehicleApp, subscribe_topic

# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)

SAFETY_FATAL_TOPIC = "safety/fatal"
DUMPER_RESPONSE_TOPIC = "dumper/dump"
LOG_PATH = "/data/logs"
DUMP_PATH = "/data/dump"


class DumperApp(VehicleApp):
    def __init__(self):
        super().__init__()

    @subscribe_topic(SAFETY_FATAL_TOPIC)
    async def on_safety_fatal_received(self, data: str) -> None:
        logger.debug(f"Event {SAFETY_FATAL_TOPIC}. Dumping to {DUMP_PATH}")

        try:
            for filename in os.listdir(LOG_PATH):
                log_file = os.path.join(LOG_PATH, filename)
                dump_file = os.path.join(DUMP_PATH, filename)

                if os.path.isfile(log_file):
                    shutil.copy2(log_file, dump_file)

            message = f"Dumped logs to {DUMP_PATH}"
            status = 0
        except Exception as e:
            logger.error(f"Failed to dump logs: {e}")
            message = f"Failed to dump logs: {e}"
            status = 1

        await self.publish_event(
            DUMPER_RESPONSE_TOPIC,
            json.dumps(
                {
                    "result": {
                        "status": status,
                        "message": message,
                    },
                }
            ),
        )


async def main():
    """Main function"""
    logger.info("Starting DumperApp...")
    # Constructing SampleApp and running it.
    vehicle_app = DumperApp()
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
