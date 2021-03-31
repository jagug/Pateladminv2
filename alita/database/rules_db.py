# Copyright (C) 2020 - 2021 Divkix. All rights reserved. Source code available under the AGPL.
#
# This file is part of Alita_Robot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from threading import RLock

from alita import LOGGER
from alita.database import MongoDB

INSERTION_LOCK = RLock()

RULES_CACHE = {}


class Rules:
    """Class for rules for chats in bot."""

    db_name = "rules"

    def __init__(self, chat_id: int) -> None:
        self.collection = MongoDB(self.db_name)
        self.chat_id = chat_id
        self.chat_info = self.__ensure_in_db()

    def get_rules(self):
        with INSERTION_LOCK:
            return self.chat_info["rules"]

    def set_rules(self, rules: str):
        with INSERTION_LOCK:
            self.chat_info["rules"] = rules
            self.collection.update({"_id": self.chat_id}, {"rules": rules})

    def get_privrules(self):
        with INSERTION_LOCK:
            return self.chat_info["privrules"]

    def set_privrules(self, privrules: bool):
        with INSERTION_LOCK:
            self.chat_info["privrules"] = privrules
            self.collection.update({"_id": self.chat_id}, {"privrules": privrules})

    def clear_rules(self):
        with INSERTION_LOCK:
            return self.collection.delete_one({"_id": self.chat_id})

    @staticmethod
    def count_chats_with_rules():
        with INSERTION_LOCK:
            collection = MongoDB(Rules.db_name)
            return collection.count({"rules": {"$regex": ".*"}})

    @staticmethod
    def count_privrules_chats():
        with INSERTION_LOCK:
            collection = MongoDB(Rules.db_name)
            return collection.count({"privrules": True})

    @staticmethod
    def count_grouprules_chats():
        with INSERTION_LOCK:
            collection = MongoDB(Rules.db_name)
            return collection.count({"privrules": False})

    @staticmethod
    def load_from_db():
        with INSERTION_LOCK:
            collection = MongoDB(Rules.db_name)
            return collection.find_all()

    def __ensure_in_db(self):
        chat_data = self.collection.find_one({"_id": self.chat_id})
        if not chat_data:
            chat_type = self.get_chat_type()
            new_data = {"_id": self.chat_id, "privrules": False, "rules": ""}
            self.collection.insert_one(new_data)
            LOGGER.info(f"Initialized Language Document for chat {self.chat_id}")
            return new_data
        return chat_data

    # Migrate if chat id changes!
    def migrate_chat(self, new_chat_id: int):
        old_chat_db = self.collection.find_one({"_id": self.chat_id})
        new_data = old_chat_db.update({"_id": new_chat_id})
        self.collection.insert_one(new_data)
        self.collection.delete_one({"_id": self.chat_id})

    @staticmethod
    def repair_db(collection):
        all_data = collection.find_all()
        keys = {"privrules": False, "rules": ""}
        for data in all_data:
            for key, val in keys.items():
                try:
                    _ = data[key]
                except KeyError:
                    LOGGER.warning(
                        f"Repairing Rules Database - setting '{key}:{val}' for {data['_id']}",
                    )
                    collection.update({"_id": data["_id"]}, {key: val})


def __check_db_status():
    LOGGER.info("Starting Rules Database Repair...")
    collection = MongoDB(Rules.db_name)
    Rules.repair_db(collection)


__check_db_status()
