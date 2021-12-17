# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: judge.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='judge.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0bjudge.proto\"z\n\x11SubmissionRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x0e\n\x06source\x18\x02 \x01(\t\x12\x0c\n\x04lang\x18\x03 \x01(\t\x12\x0f\n\x07problem\x18\x04 \x01(\t\x12\x12\n\nattachment\x18\x05 \x01(\x08\x12\x10\n\x08\x66ilename\x18\x06 \x01(\t\"&\n\x10SubmissionResult\x12\x12\n\nfinalScore\x18\x01 \x01(\x05\x32@\n\x0cJudgeService\x12\x30\n\x05judge\x12\x12.SubmissionRequest\x1a\x11.SubmissionResult\"\x00\x62\x06proto3'
)




_SUBMISSIONREQUEST = _descriptor.Descriptor(
  name='SubmissionRequest',
  full_name='SubmissionRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='username', full_name='SubmissionRequest.username', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='source', full_name='SubmissionRequest.source', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lang', full_name='SubmissionRequest.lang', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='problem', full_name='SubmissionRequest.problem', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='attachment', full_name='SubmissionRequest.attachment', index=4,
      number=5, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='filename', full_name='SubmissionRequest.filename', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=15,
  serialized_end=137,
)


_SUBMISSIONRESULT = _descriptor.Descriptor(
  name='SubmissionResult',
  full_name='SubmissionResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='finalScore', full_name='SubmissionResult.finalScore', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=139,
  serialized_end=177,
)

DESCRIPTOR.message_types_by_name['SubmissionRequest'] = _SUBMISSIONREQUEST
DESCRIPTOR.message_types_by_name['SubmissionResult'] = _SUBMISSIONRESULT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SubmissionRequest = _reflection.GeneratedProtocolMessageType('SubmissionRequest', (_message.Message,), {
  'DESCRIPTOR' : _SUBMISSIONREQUEST,
  '__module__' : 'judge_pb2'
  # @@protoc_insertion_point(class_scope:SubmissionRequest)
  })
_sym_db.RegisterMessage(SubmissionRequest)

SubmissionResult = _reflection.GeneratedProtocolMessageType('SubmissionResult', (_message.Message,), {
  'DESCRIPTOR' : _SUBMISSIONRESULT,
  '__module__' : 'judge_pb2'
  # @@protoc_insertion_point(class_scope:SubmissionResult)
  })
_sym_db.RegisterMessage(SubmissionResult)



_JUDGESERVICE = _descriptor.ServiceDescriptor(
  name='JudgeService',
  full_name='JudgeService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=179,
  serialized_end=243,
  methods=[
  _descriptor.MethodDescriptor(
    name='judge',
    full_name='JudgeService.judge',
    index=0,
    containing_service=None,
    input_type=_SUBMISSIONREQUEST,
    output_type=_SUBMISSIONRESULT,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_JUDGESERVICE)

DESCRIPTOR.services_by_name['JudgeService'] = _JUDGESERVICE

# @@protoc_insertion_point(module_scope)
