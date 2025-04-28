# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

import sqlite3
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import requests
import random
import re

class ActionSaveReservation(Action):
    """
    Action pour enregistrer une réservation
    """

    def name(self) -> Text:
        return "action_save_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Save reservation action triggered")
        
        # Récupérer les slots
        rest_date = tracker.get_slot("rest_date")
        rest_hour = tracker.get_slot("rest_hour")
        persons = tracker.get_slot("persons")
        name = tracker.get_slot("name")
        phone_number = tracker.get_slot("phone_number")
        comment = tracker.get_slot("comment")
        
        # Connexion à la base de données SQLite
        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()

        # Check if the reservation already exists
        cursor.execute("""
            SELECT * FROM reservation
            WHERE date = ? AND heure = ? AND nbr_personne = ? AND nom_reservation = ? AND num_telephone = ?
        """, (rest_date, rest_hour, persons, name, phone_number))
        existing_reservation = cursor.fetchone()
        if existing_reservation:
            dispatcher.utter_message(text="Une réservation existe déjà avec le même numéro de téléphone.")
            connection.close()
            return []
        
        # si le commentaire est vide mettre "sans commentaire"
        if not comment:
            comment = "sans commentaire"

        # Insérer les données dans la table
        try:
            cursor.execute("""
                INSERT INTO reservation (date, nbr_personne, heure, nom_reservation, num_telephone, commentaire)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rest_date, persons, rest_hour, name, phone_number, comment))
            connection.commit()
            reservation_id = cursor.lastrowid
            dispatcher.utter_message(text=f"Votre réservation a été enregistrée avec succès. Votre numéro de réservation est: {reservation_id}")
        except Exception as e:
            dispatcher.utter_message(text=f"Une erreur est survenue lors de l'enregistrement : {e}")
        finally:
            connection.close()

        print(f"Reservation details: {rest_date}, {rest_hour}, {persons}, {name}, {phone_number}, {comment}")

        return []
    
class ActionValidateReservationNumber(Action):
    """
    Action pour valider le numéro de réservation
    """

    def name(self) -> Text:
        return "action_validate_reservation_number"

    def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        print(f"Validate reservation number action triggered")

        reservation_number = tracker.get_slot("number_reservation")
        is_valid = self._check_reservation_number(reservation_number)
        
        intent_sequence = [e.get("parse_data", {}).get("intent", {}).get("name") 
                          for e in tracker.events if e.get("event") == "user"]
        
        for intent in reversed(intent_sequence):
            if intent != "provide_number_reservation":
                initial_intent = intent
                break
        else:
            initial_intent = "unknown"
        
        print(f"Intent initial: {initial_intent}, Numéro valide: {is_valid}")
        
        if is_valid:
            if initial_intent == "modify_reservation":
                return [
                    SlotSet("reservation_valid", True),
                    FollowupAction("utter_ask_new_comment")
                ]
            elif initial_intent == "cancel_reservation":
                return [
                    SlotSet("reservation_valid", True),
                    FollowupAction("utter_confirm_cancel_reservation")
                ]
            elif initial_intent == "show_reservation_details":
                return [
                    SlotSet("reservation_valid", True),
                    FollowupAction("action_show_reservation_details")
                ]
            else:
                return [SlotSet("reservation_valid", True)]
        else:
            dispatcher.utter_message(text="Ce numéro de réservation n'est pas valide.")
            return [SlotSet("reservation_valid", False),
                    FollowupAction("utter_ask_number_reservation")
]

    def _check_reservation_number(self, number):
        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM reservation WHERE num_reservation = ?", (number,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"Erreur lors de la vérification du numéro de réservation : {e}")
            return False
        finally:
            connection.close()


class ActionCancelReservation(Action):
    """
    Action pour annuler une réservation
    """
    def name(self) -> Text:
        return "action_cancel_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Cancel reservation action triggered")
        
        reservation_number = tracker.get_slot("number_reservation")

        # Connexion à la base de données SQLite
        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()

        try:
            cursor.execute("DELETE FROM reservation WHERE num_reservation = ?", (reservation_number,))
            connection.commit()
            if cursor.rowcount > 0:
                dispatcher.utter_message(text=f"La réservation {reservation_number} a été annulée.")
            else:
                dispatcher.utter_message(text="Aucune réservation trouvée avec ce numéro.")
        except Exception as e:
            dispatcher.utter_message(text=f"Une erreur est survenue lors de l'annulation : {e}")   
        finally:
            connection.close()
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

        print(f"Menu of the day action triggered")

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

class ActionUpdateCommentReservation(Action):
    '''
    action pour mettre à jour le commentaire d'une réservation
    '''
    def name(self) -> Text:
        return "action_update_comment_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print("Update reservation comment action triggered")

        reservation_number = tracker.get_slot("number_reservation")
        new_comment = tracker.get_slot("comment")

        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()

        try:
            cursor.execute("""
                UPDATE reservation
                SET commentaire = ?
                WHERE num_reservation = ?
            """, (new_comment, reservation_number))
            connection.commit()
            dispatcher.utter_message(text="Le commentaire de votre réservation a bien été mis à jour.")
        except Exception as e:
            dispatcher.utter_message(text="Erreur lors de la mise à jour du commentaire.")
            print(e)
        finally:
            connection.close()
        
        return []


class ActionValidatePhoneNumber(Action):
    '''
    Action pour valider le numéro de téléphone
    '''
    def name(self) -> Text:
        return "action_validate_phone_number"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        phone_number = tracker.get_slot("phone_number")
        
        if phone_number:
            cleaned_number = re.sub(r'\s', '', phone_number)
            # transforme tel:+3306152524|+3306152524 en +3306152524 pour ce faire il va récupérer tout ce qui est après le pipe
            if "|" in cleaned_number:
                cleaned_number = cleaned_number.split("|")[1]
                
            is_valid = bool(re.match(r'^(0|\+33|\+330)[1-9][0-9]{8}$', cleaned_number))
            print(f"Numéro de téléphone : {cleaned_number}, valide : {is_valid}")
            
            if is_valid:
                formatted_number = self._format_phone_number(cleaned_number)
                return [SlotSet("phone_number", formatted_number),
                        SlotSet("phone_valid", True), 
                        FollowupAction("utter_booked_restaurant_add_comment")]
        dispatcher.utter_message(text="Le numéro de téléphone n'est pas valide.")
        return [SlotSet("phone_valid", False),
                FollowupAction("utter_booked_restaurant_phone_number")
]    
    def _format_phone_number(self, number):
        if number.startswith('+33'):
            return number
        else:
            return ' '.join([number[i:i+2] for i in range(0, 10, 2)])
    


class ActionShowReservationDetails(Action):
    """
    Action pour afficher les détails d'une réservation à partir de son numéro
    """
    def name(self) -> Text:
        return "action_show_reservation_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        reservation_number = tracker.get_slot("number_reservation")
        
        # Connexion à la base de données
        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()
        
        try:
            # Requête pour récupérer les détails de la réservation
            cursor.execute("""
                SELECT date, nbr_personne, heure, nom_reservation, num_telephone, commentaire
                FROM reservation
                WHERE num_reservation = ?
            """, (reservation_number,))
            
            result = cursor.fetchone()
            
            date, nbr_personnes, heure, nom, telephone, commentaire = result
            
            # Construction du message
            details = f"Voici les détails de votre réservation n°{reservation_number} :\n"
            details += f"📅 Date : {date}\n"
            details += f"🕒 Heure : {heure}\n"
            details += f"👥 Nombre de personnes : {nbr_personnes}\n"
            details += f"👤 Au nom de : {nom}\n"
            details += f"📞 Téléphone : {telephone}\n"
            
            if commentaire:
                details += f"💬 Commentaire : {commentaire}"
            else:
                details += "💬 Aucun commentaire"
                        
            # Envoyer le message avec les détails
            dispatcher.utter_message(text=details)
            return []
                
        except Exception as e:
            dispatcher.utter_message(text=f"Une erreur est survenue lors de la recherche de votre réservation : {e}")
            return []
        finally:
            connection.close()