import os

import click
from elasticsearch_dsl import Q, Search, connections
from graphql_relay import to_global_id

from graphql_api.config import ES_ENDPOINT

connections.create_connection(hosts=ES_ENDPOINT)


@click.group()
def slt():
    pass


@slt.command(name='ohs')
@click.option(
    '-f', '--filter', type=click.Choice(['DAG', 'HAZ'], case_sensitive=False), help='list filter solutions by subtype.'
)
@click.option(
    '-l', '--list-ids', is_flag=True, default=False, help="list the toshi_ids, with no aggregation (verbose option)."
)
@click.option('-v', '--verbose', is_flag=True, default=False, help='print extra information.')
def cli_OHS(filter, list_ids, verbose):
    """Get OpenquakeHazardSolution hits - either hazard or disagg."""
    s = Search()
    qFilter = Q("term", meta__k="hazard_agg_target")  # this marks a disagg
    qClass = Q("term", clazz_name__keyword="OpenquakeHazardSolution")
    if filter and filter == 'DAG':
        if verbose:
            click.echo('GET disagggregation solutions')
    elif filter and filter == 'HAZ':
        if verbose:
            click.echo('GET hazard solutions')
        qFilter = ~qFilter  # invert for hazard / non-disaggs

    expr = qClass & qFilter if filter else qClass
    s = s.query(expr)

    # the shortform, just dump the ids to stdout
    if list_ids:
        for hit in s.scan():
            if verbose:
                click.echo(f'{to_global_id(hit.clazz_name, hit.id)}, {hit.clazz_name}, {hit.id}')
            else:
                click.echo(to_global_id(hit.clazz_name, hit.id))
        return

    # the longform, aggregate by month ...
    s.aggs.bucket('solutions_per_month', 'date_histogram', field='created', interval='month')
    s = s.extra(explain=True, track_total_hits=True)

    if verbose:
        click.echo('query')
        click.echo(s.to_dict())

    s = s[:2]

    response = s.execute()
    click.echo(f'Total {response.hits.total.value} hits found.')
    click.echo()
    for bucket in response.aggregations.solutions_per_month.buckets:
        click.echo(f'{bucket.key_as_string}, {bucket.doc_count}')

    if verbose:
        for hit in response:
            click.echo(f'{hit}, {hit.created}, {hit.clazz_name}')


if __name__ == '__main__':
    slt()  # pragma: no cover
