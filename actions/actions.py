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

class ActionSaveReservation(Action):
    """
    Action to save reservation details in the SQLite database.
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
            dispatcher.utter_message(text="Votre réservation a été enregistrée avec succès.")
        except Exception as e:
            dispatcher.utter_message(text=f"Une erreur est survenue lors de l'enregistrement : {e}")
        finally:
            connection.close()

        print(f"Reservation details: {rest_date}, {rest_hour}, {persons}, {name}, {phone_number}, {comment}")

        return []

class ActionHelloWorld(Action):
    """
    Action to respond with a hello world message.
    """

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"Hello world action triggered")
        return []

class ActionGetReservations(Action):
    """
    Action to retrieve all reservations from the SQLite database.
    """

    def name(self) -> Text:
        return "action_get_reservations"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Get reservations action triggered")

        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()
        
        try:
            cursor.execute("SELECT * FROM reservation")
            reservations = cursor.fetchall()
            for reservation in reservations:
                dispatcher.utter_message(text=f"Reservation: {reservation}")
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while retrieving reservations: {e}")
        finally:
            connection.close()
        
        return []
    
class ActionCheckExistingReservation(Action):
    """
    Action to check if a reservation already exists in the SQLite database.
    """

    def name(self) -> Text:
        return "action_check_existing_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Check existing reservation action triggered")

        rest_date = tracker.get_slot("rest_date")
        rest_hour = tracker.get_slot("rest_hour")
        persons = tracker.get_slot("persons")
        name = tracker.get_slot("name")
        telephone = tracker.get_slot("phone_number")

        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM reservation
                WHERE date = ? AND heure = ? AND nbr_personne = ? AND nom_reservation = ? AND num_telephone = ?
            """, (rest_date, rest_hour, persons, name, telephone))
            existing_reservations = cursor.fetchall()
            if existing_reservations:
                dispatcher.utter_message(text="Une réservation existe déjà avec le même numéro de téléphone.")
            else:
                dispatcher.utter_message(text="Aucune réservation trouvée pour ces détails.")
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while checking reservations: {e}")
        finally:
            connection.close()
        
        return []
    
class ActionUpdateReservation(Action):
    """
    Action to update an existing reservation in the SQLite database.
    """

    def name(self) -> Text:
        return "action_update_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Update reservation action triggered")

        rest_date = tracker.get_slot("rest_date")
        rest_hour = tracker.get_slot("rest_hour")
        persons = tracker.get_slot("persons")
        name = tracker.get_slot("name")

        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                UPDATE reservation
                SET date = ?, nbr_personne = ?, heure = ?, nom_reservation = ?
                WHERE date = ? AND heure = ? AND nbr_personne = ? AND nom_reservation = ?
            """, (rest_date, persons, rest_hour, name, rest_date, rest_hour, persons, name))
            connection.commit()
            dispatcher.utter_message(text="Votre réservation a été mise à jour avec succès.")
        except Exception as e:
            dispatcher.utter_message(text=f"Une erreur est survenue lors de la mise à jour : {e}")
        finally:
            connection.close()
        
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
        # Connexion à la base de données SQLite
        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM reservation WHERE id = ?", (number,))
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
            cursor.execute("DELETE FROM reservation WHERE id = ?", (reservation_number,))
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
    
class ActionCheckAndHandleReservation(Action):
    def name(self) -> Text:
        return "action_check_and_handle_reservation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        rest_date = tracker.get_slot("rest_date")
        rest_hour = tracker.get_slot("rest_hour")
        persons = tracker.get_slot("persons")
        name = tracker.get_slot("name")

        connection = sqlite3.connect("rasa-reservation.db")
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT * FROM reservation
                WHERE date = ? AND heure = ? AND nbr_personne = ? AND nom_reservation = ?
            """, (rest_date, rest_hour, persons, name))
            existing = cursor.fetchone()

            if existing:
                dispatcher.utter_message(text="Une réservation existe déjà avec ces détails. Souhaitez-vous choisir une autre date ?")
                return [SlotSet("reservation_valid", False)]
            else:
                return [SlotSet("reservation_valid", True), FollowupAction("action_save_reservation")]
        except Exception as e:
            dispatcher.utter_message(text="Erreur lors de la vérification de réservation.")
            print(e)
            return []
        finally:
            connection.close()

class ActionUpdateCommentReservation(Action):
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
                WHERE id = ?
            """, (new_comment, reservation_number))
            connection.commit()
            dispatcher.utter_message(text="Le commentaire de votre réservation a bien été mis à jour.")
        except Exception as e:
            dispatcher.utter_message(text="Erreur lors de la mise à jour du commentaire.")
            print(e)
        finally:
            connection.close()
        
        return []
    
