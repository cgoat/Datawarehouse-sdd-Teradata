{# 1..5 quintile bin via ROW_NUMBER + COUNT_OVER. Replaces NTILE(5),
   which this Teradata instance does not support. #}
{% macro quintile(expr, direction='ASC') %}
CAST(CEILING(
    5.0
    * CAST(ROW_NUMBER() OVER (ORDER BY {{ expr }} {{ direction }}) AS FLOAT)
    / NULLIF(CAST(COUNT(*) OVER () AS FLOAT), 0)
) AS INTEGER)
{% endmacro %}
