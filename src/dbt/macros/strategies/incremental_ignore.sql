{% materialization incremental_ignore, default %}


  {%- set identifier = model['alias'] -%}
  {%- set tmp_identifier = model['name'] + '__dbt_tmp' -%}
  {%- set backup_identifier = model['name'] + '__dbt_backup' -%}
  {%- set unique_list = model.config['unique_list'] -%}
  {{ log('unique list: ' ~ unique_list, info=true) }}

  {%- set old_relation = adapter.get_relation(database=database, schema=schema, identifier=identifier) -%}
  {%- set target_relation = api.Relation.create(identifier=identifier, schema=schema, database=database, type='table') -%}
  {%- set intermediate_relation = api.Relation.create(identifier=tmp_identifier, schema=schema, database=database, type='table') -%}

  {%- set preexisting_intermediate_relation = adapter.get_relation(identifier=tmp_identifier, schema=schema, database=database) -%}

  {%- set backup_relation_type = 'table' if old_relation is none else old_relation.type -%}
  {%- set backup_relation = api.Relation.create(identifier=backup_identifier, schema=schema, database=database, type=backup_relation_type) -%}
  {%- set preexisting_backup_relation = adapter.get_relation(identifier=backup_identifier, schema=schema, database=database) -%}

  {{ drop_relation_if_exists(preexisting_intermediate_relation) }}
  {{ drop_relation_if_exists(preexisting_backup_relation) }}

  {% if old_relation is none %}
    {%- set error_msg = target_relation | upper ~ ' does not exist - please create it in the target database/schema first.' -%}
    {{ exceptions.raise_compiler_error(error_msg) }}
  {% endif %}

  {{ run_hooks(pre_hooks, inside_transaction=False) }}

  -- `BEGIN` happens here:
  {{ run_hooks(pre_hooks, inside_transaction=True) }}

  -- build the intermediate relation
  {% call statement('main') -%}
    {{ get_create_table_as_sql(False, intermediate_relation, sql) }}
  {%- endcall %}

  -- build the backup relation
  {% call statement('backup_old_relation') -%}
    create table {{ backup_relation }} as select * from {{ old_relation }};
  {%- endcall %}

  -- insert into the target relation selecting from the intermediate relation
  {%- set col_list = [] -%}
  {%- set columns_in_intermediate_relation = adapter.get_columns_in_relation(intermediate_relation) -%}
  {%- for col in columns_in_intermediate_relation -%}
    {%- do col_list.append(col.name) -%}
  {%- endfor -%}

  {%- if col_list | length > 0 -%}
    {{ log('incremental_ignore model ' ~ target_relation ~ '.....inserting rows', info=true) }}
    {%- call statement('insert_rows') -%}
      insert into {{ target_relation }} ({{ col_list | join(", ") }}) select {{ col_list | join(", ") }} from {{ intermediate_relation }} where ({{ unique_list | join(", ") }}) not in (select {{ unique_list | join(", ") }} from {{ target_relation }});
    {%- endcall -%}
    {{ log('incremental_ignore model ' ~ target_relation ~ '.....inserted rows', info=true) }}
  {%- endif -%}

  -- cleanup
  {{ drop_relation_if_exists(intermediate_relation) }}

  {% do create_indexes(target_relation) %}

  {{ run_hooks(post_hooks, inside_transaction=True) }}

  {% do persist_docs(target_relation, model) %}

  -- `COMMIT` happens here
  {{ adapter.commit() }}

  -- finally, drop the existing/backup relation after the commit
  {{ drop_relation_if_exists(backup_relation) }}

  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}