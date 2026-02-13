import pytest

from exasol_udf_mock_python.column import Column
from exasol_udf_mock_python.group import Group
from exasol_udf_mock_python.mock_exa_environment import MockExaEnvironment, Connection
from exasol_udf_mock_python.mock_meta_data import MockMetaData
from exasol_udf_mock_python.udf_mock_executor import UDFMockExecutor

def test_emit_not_allowed():
    def udf_wrapper():
        {% macro someop() %}{% include "exa_py_list.py" %}{% endmacro %}
        {{ someop()|indent(8) }}

    executor = UDFMockExecutor()
    meta = MockMetaData(
        script_code_wrapper_function=udf_wrapper,
        input_type="SCALAR",
        input_columns=[Column("connection_name", str, "VARCHAR(128)")],
        output_type="EMITS",
        output_columns=[
            Column("object_name", str, "varchar(1000)"),
            Column("searchable", bool, "boolean"),
            Column("updateable", bool, "boolean"),
            Column("object_label", str, "varchar(1000)")
        ]
    )
    exa = MockExaEnvironment(
        meta,
        connections={
            "HELLO_CON": Connection(
                # ---- YOUR ORGANIZATION HERE ----
                address="https://arglbargl.sandbox.my.salesforce.com",
                # ---- YOUR SF ACCESS TOKEN HERE -----
                password="00DbY[...]DUbfa_"
            )
        }
    )
    # with pytest.raises(RuntimeError):
    result = executor.run([Group([('HELLO_CON',),])], exa)
    assert(result == 20)
    # print(f'{result}')
