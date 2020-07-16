import cerberus
import json

from citrine_daemon.util import encode_tensor, decode_tensor

tensor_type = cerberus.TypeDefinition('tensor', (dict,), ())

np_dtypes = [
    'int8', 'int16', 'int32', 'int64', 
    'uint8', 'uint16', 'uint32', 'uint64', 
    'float16', 'float32', 'float64', 'float128', 
    # dropping non-real-number types
]

tensor_schema = {
    # discount tensorproto
    'dtype': {
        'type': 'string',
        'allowed': np_dtypes,
    },
    'data': {
        'type': 'string',
    },
    'shape': {
        'type': 'list',
        'schema': {
            'type': 'integer',
        }
    }
}


class CitrineValidator(cerberus.Validator):
    types_mapping = cerberus.Validator.types_mapping.copy()
    types_mapping['tensor'] = tensor_type

    def _validate_tensor(self, schema, field, value):
        """
        Cerberus inspects docs to get the meta-schema
        This next line is special, don't change it or add anything after it until the end of the doc
        The rule's arguments are validated against this schema:
        {
            'type': 'dict',
            'schema': {
                'dtype': {
                    'required': False,
                    'nullable': True,
                    'default': None,
                    'allowed': NP_DTYPES,
                },
                'shape': {
                    'required': False,
                    'nullable': True,
                    'default': None,
                    'type': 'list',
                    'schema': {
                        'type': 'integer',
                        'nullable': True,
                    },
                },
            },
        }
        """
        if value is None:
            return

        value_validator = cerberus.Validator(schema=tensor_schema)
        if not value_validator.validate(value):
            return self._error(field, json.dumps(value_validator.errors, indent=4))
        
        if schema['shape'] is not None:
            if len(value['shape']) != len(schema['shape']):
                return self._error(
                    field, 
                    f'{field} expects a rank {len(schema["shape"])} tensor, instead got rank {len(value["shape"])}'
                )
            for actual, expected in zip(value['shape'], schema['shape']):
                if expected is not None and actual != expected:
                    return self._error(
                        field, 
                        f'{field} was expecting shape {schema["shape"]}, instead got shape {value["shape"]}'
                    )

        if schema['dtype'] is not None:
            if value['dtype'] != schema['dtype']:
                expect_dtype = schema['dtype']
                actual_dtype = value['dtype']
                return self._error(field, f'{field} should have dtype {expect_dtype} but instead got {actual_dtype}')
            
        ref = self.root_document
        for refpath in self.document_path:
            ref = ref[refpath]
        ref[field] = decode_tensor(value)

    _validate_tensor.__doc__ = _validate_tensor.__doc__.replace('NP_DTYPES', str(np_dtypes))
