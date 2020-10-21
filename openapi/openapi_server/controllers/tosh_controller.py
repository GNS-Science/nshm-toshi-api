import connexion
import six

from openapi_server.models.api_response import ApiResponse  # noqa: E501
from openapi_server.models.tosh import Tosh  # noqa: E501
from openapi_server import util


def add_tosh(body):  # noqa: E501
    """Add a new tosh to the store

     # noqa: E501

    :param body: Tosh object that needs to be added to the store
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Tosh.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_tosh(tosh_id, api_key=None):  # noqa: E501
    """Deletes a tosh

     # noqa: E501

    :param tosh_id: Tosh id to delete
    :type tosh_id: int
    :param api_key: 
    :type api_key: str

    :rtype: None
    """
    return 'do some magic!'


def find_toshs_by_status(status):  # noqa: E501
    """Finds Toshs by status

    Multiple status values can be provided with comma separated strings # noqa: E501

    :param status: Status values that need to be considered for filter
    :type status: List[str]

    :rtype: List[Tosh]
    """
    return 'do some magic!'


def get_tosh_by_id(tosh_id):  # noqa: E501
    """Find tosh by ID

    Returns a single tosh # noqa: E501

    :param tosh_id: ID of tosh to return
    :type tosh_id: int

    :rtype: Tosh
    """
    return 'do some magic!'


def update_tosh(body):  # noqa: E501
    """Update an existing tosh

     # noqa: E501

    :param body: Tosh object that needs to be added to the store
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Tosh.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_tosh_with_form(tosh_id, name=None, status=None):  # noqa: E501
    """Updates a tosh in the store with form data

     # noqa: E501

    :param tosh_id: ID of tosh that needs to be updated
    :type tosh_id: int
    :param name: Updated name of the tosh
    :type name: str
    :param status: Updated status of the tosh
    :type status: str

    :rtype: None
    """
    return 'do some magic!'


def upload_file(tosh_id, additional_metadata=None, file=None):  # noqa: E501
    """uploads an image

     # noqa: E501

    :param tosh_id: ID of tosh to update
    :type tosh_id: int
    :param additional_metadata: Additional data to pass to server
    :type additional_metadata: str
    :param file: file to upload
    :type file: str

    :rtype: ApiResponse
    """
    return 'do some magic!'
