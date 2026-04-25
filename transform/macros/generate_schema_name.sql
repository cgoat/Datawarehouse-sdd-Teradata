{#
  Treat +schema values as absolute database names, not suffixes.
  Default dbt behavior concatenates target.schema + custom_schema — we want
  models to land exactly in DW_BRONZE / DW_SILVER / DW_GOLD regardless of target.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
