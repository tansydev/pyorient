__author__ = 'Ostico'

from ConnectMessage import *
from Fields.SendingField import SendingField
from Fields.ReceivingField import ReceivingField
from Fields.OrientOperations import *
from Fields.OrientPrimitives import *
from pyorient.OrientSocket import OrientSocket


class DbOpenMessage(BaseMessage):

    def __init__(self, conn_message):

        self._session_id = -1
        self._user = ''
        self._pass = ''
        self._client_id = ''
        self._db_name = ''
        self._db_type = DB_TYPE_DOCUMENT

        # already connected and the ConnectMessage instance was provided
        if isinstance( conn_message, ConnectMessage ):
            super( DbOpenMessage, self ).\
                __init__(conn_message.get_orient_socket_instance())

            self._user = conn_message._user
            self._pass = conn_message._pass
            self._client_id = conn_message._client_id

            self._protocol = conn_message.get_protocol()  # get from cache
            self._session_id = conn_message.fetch_response()  # get from cache

            self.append( SendingField( ( BYTE, DB_OPEN ) ) )

            # session_id
            self.append( SendingField( ( INT, self._session_id ) ) )

        elif isinstance( conn_message, OrientSocket ):

            super( DbOpenMessage, self ).__init__(conn_message)
            # this block of code check for session because this class
            # can be initialized directly from orient socket
            if self._session_id < 0:
                # try to connect, we inherited BaseMessage
                conn_message = ConnectMessage( self._orientSocket )
                self._session_id = conn_message\
                    .prepare( ( self._user, self._pass, self._client_id ) )\
                    .send_message().fetch_response()

                self._protocol = conn_message.get_protocol()
                self.append( SendingField( ( BYTE, DB_OPEN ) ) )

                # session_id
                self.append( SendingField( ( INT, self._session_id ) ) )

    def prepare(self, params=None ):

        if isinstance( params, tuple ):
            try:
                self._user = params[0]
                self._pass = params[1]
                self._client_id = params[2]
                self._db_name = params[3]
                self._db_type = params[4]
            except IndexError:
                # Use default for non existent indexes
                pass

        self.append(
            SendingField( ( STRINGS, [NAME, VERSION] ) )
        ).append(
            SendingField( ( SHORT, SUPPORTED_PROTOCOL ) )
        ).append(
            SendingField( (STRINGS, [self._client_id, self._db_name,
                                     self._db_type, self._user, self._pass]) )
        )
        return super( DbOpenMessage, self ).prepare()

    def fetch_response(self):
        self._set_response_header_fields()
        self.append( ReceivingField( INT ) )  # session_id
        self.append( ReceivingField( SHORT ) )  # cluster_num

        self._session_id, cluster_num = \
            super( DbOpenMessage, self ).fetch_response()

        self._reset_fields_definition()

        for n in range(0, cluster_num):
            self.append( ReceivingField( STRING ) )  # cluster_name
            self.append( ReceivingField( SHORT ) )  # cluster_id
            self.append( ReceivingField( STRING ) )  # cluster_type
            self.append( ReceivingField( SHORT ) )  # cluster_segment_id

        self.append( ReceivingField( INT ) )  # cluster config string ( -1 )
        self.append( ReceivingField( STRING ) )  # cluster release

        response = super( DbOpenMessage, self ).fetch_response(True)

        clusters = []
        for n in range(0, cluster_num):
            x = n * 4
            cluster_name = response[x]
            cluster_id = response[x + 1]
            cluster_type = response[x + 2]
            cluster_segment_data_id = response[x + 3]
            clusters.append({
                "name": cluster_name,
                "id": cluster_id,
                "type": cluster_type,
                "segment": cluster_segment_data_id
            })

        return clusters

    def set_db_name(self, db_name):
        self._db_name = db_name

    def set_db_type(self, db_type):
        self._db_name = db_type

    def set_client_id(self, _cid):
        self._client_id = _cid
        return self

    def set_user(self, _user):
        self._user = _user
        return self

    def set_pass(self, _pass):
        self._pass = _pass
        return self