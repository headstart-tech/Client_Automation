"""
this file contains all functions regarding user audit trails using celery.
"""

import pika
import json
from app.core.celery_app import celery_app
from app.core.utils import settings, utility_obj, logger
from app.database.configuration import DatabaseConfiguration


class UserAuditTrail:
    """
    Contain functions related to user audit trail

    This class is responsible for managing user audit logs, specifically by interacting with RabbitMQ to consume
    messages and then storing those messages in a MongoDB collection.
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def add_user_audit_logs(queue_name: str) -> None:
        """
        Retrieves user audit messages from RabbitMQ and stores them in MongoDB.

        This method performs the following operations:
        1. Establishes a connection to the RabbitMQ server using the credentials and URL provided in the settings.
        2. Declares the 'user_audit_queue' if it does not already exist.
        3. Continuously retrieves messages from the 'user_audit_queue' until no more messages are available.
        4. Processes each message by appending it to a list and acknowledging receipt.
        5. Inserts the list of processed messages into the MongoDB user audit collection.
        6. Handles any exceptions that occur during message retrieval, processing, or database insertion, logging errors
           as needed.

        Params:
            queue_name (str): The name of the RabbitMQ queue to consume from.

        Exceptions:
            - pika.exceptions.AMQPConnectionError: Raised if there is a connection error with RabbitMQ.
            - pika.exceptions.AMQPChannelError: Raised if there is an issue with the RabbitMQ channel.
            - pika.exceptions.AMQPError: General errors related to AMQP.
            - Exception: Catches any other unexpected errors that occur during the process.

        Returns:
            None
        """
        try:
            url = (f"amqp://{settings.rmq_username}:{settings.rmq_password}@{settings.rmq_url}:{settings.rmq_port}/"
                   f"{settings.rmq_host}")
            connection = pika.BlockingConnection(pika.URLParameters(url))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            messages = []
            while True:
                method_frame, header_frame, body = channel.basic_get(queue=queue_name)
                if method_frame:
                    try:
                        data = utility_obj.format_data(body)
                        messages.append(data)
                        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    except Exception as e:
                        logger.error(f"Error processing message from {queue_name}: {e}")
                        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                else:
                    logger.info(f"No more messages in the queue: {queue_name}.")
                    break
            if queue_name == "role_permission_logs":
                DatabaseConfiguration().rbac_audit_collection.insert_many(messages)
            else:
                DatabaseConfiguration().user_audit_collection.insert_many(messages)
            logger.info(f"Successfully inserted data from {queue_name} into MongoDB")
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}")
        except pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error: {e}")
        except pika.exceptions.AMQPError as e:
            logger.error(f"AMQP error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

