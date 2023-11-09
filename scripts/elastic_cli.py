import os
import click

from graphql_api.config import ES_ENDPOINT
from elasticsearch_dsl import Search
from elasticsearch_dsl import connections, Q

connections.create_connection(hosts=ES_ENDPOINT)

@click.group()
def slt():
    pass

@slt.command(name='ohs')
@click.option('-D', '--disaggs', is_flag=True)
@click.option('-v', '--verbose', is_flag=True)
def cli_OHS(disaggs, verbose):
    """Get OpenquakeHazardSolution hits - either hazard or disagg."""
    s = Search()
    q1 = Q("term", meta__k="hazard_agg_target") # this marks a disagg
    q2 = Q("term", clazz_name__keyword="OpenquakeHazardSolution")
    if disaggs:
        click.echo('GET disagggregation solutions')
    else:
        click.echo('GET hazard solutions')
        q1 = ~q1 # invert for hazard / non-disaggs
    s = s.query( q2 & q1)
    # aggregate by month ...
    s.aggs.bucket('solutions_per_month', 'date_histogram', field='created', interval='month')
    s = s.extra(explain=True, track_total_hits=True)

    if verbose:
        click.echo('query')
        click.echo(s.to_dict())

    s = s[:2]

    response = s.execute()
    click.echo(f'Total {response.hits.total.value} hits found.' )
    click.echo()
    for bucket in response.aggregations.solutions_per_month.buckets:
        click.echo(f'{bucket.key_as_string}, {bucket.doc_count}')
    
    if verbose:
        for hit in response:
            click.echo(f'{hit}, {hit.created}, {hit.clazz_name}')


if __name__ == '__main__':
    slt()  # pragma: no cover