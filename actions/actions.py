# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import requests
import random


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
    
class ActionAskMenuOfDay(Action):
    """
    Action pour demander le menu du jour
    """
    def name(self) -> Text:
        return "action_menu_of_day"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # exécuter une requête vers 'https://dummyjson.com/recipes/tag/Italian'

        try:
            responseMenu = requests.get('https://dummyjson.com/recipes/tag/Italian')
            dataMenu = responseMenu.json()
            menuSelect = random.choice(dataMenu['recipes'])
            print(menuSelect)

            responseDessert = requests.get('https://dummyjson.com/recipes/meal-type/Dessert')
            dataDessert = responseDessert.json()
            dessertSelect = random.choice(dataDessert['recipes'])

            menu = f"Plat du jour : {menuSelect['name']}\nIngrédients : {', '.join(menuSelect['ingredients'])}\n\nDessert du jour : {dessertSelect['name']}\nIngrédients : {', '.join(dessertSelect['ingredients'])}"
            dispatcher.utter_message(text=f"Voici le menu du jour :\n{menu}")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="Désolé, je n'ai pas pu récupérer le menu du jour.")
            print(f"Erreur lors de la récupération du menu : {e}")
        return []