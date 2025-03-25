# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction


class ActionValidateReservationNumber(Action):
    """
    Action pour valider le numéro de réservation
    """

    def name(self) -> Text:
        return "action_validate_reservation_number"

    def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        reservation_number = tracker.get_slot("number_reservation")
        is_valid = self._check_reservation_number(reservation_number)
        
        if is_valid:
            return [SlotSet("reservation_valid", True), 
                    FollowupAction("utter_confirm_cancel_reservation")
            ]
        else:
            dispatcher.utter_message(text="Ce numéro de réservation n'est pas valide.")
            return [SlotSet("reservation_valid", False),
                    FollowupAction("utter_ask_number_reservation")
]

    def _check_reservation_number(self, number):
        # TODO: vérifier en base
        try:
            num = int(number)
            return 1000 <= num <= 9999
        except:
            return False


class ActionCancelReservation(Action):
    """
    Action pour annuler une réservation
    """
    def name(self) -> Text:
        return "action_cancel_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        reservation_number = tracker.get_slot("number_reservation")
        # TODO: supprimer la réservation en base
        dispatcher.utter_message(text=f"La réservation {reservation_number} a été annulée.")
        return []