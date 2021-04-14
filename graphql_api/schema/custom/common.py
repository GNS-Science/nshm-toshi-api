import graphene

class GitReferences():
    """Source code git references (from `git log --oneline -1`)"""
    opensha_ucerf3 = graphene.String(
        description="git ref for opensha-ucerf3")
    opensha_commons = graphene.String(
        description="git ref for opensha-commons")
    opensha_core = graphene.String(
        description="git ref for opensha-core")
    nshm_nz_opensha = graphene.String(
        description="git ref for nshm-nz-opensha")

class GitReferencesInput(GitReferences, graphene.InputObjectType):
    """Arguments passed into the opensha Rupture Generator"""

class GitReferencesOutput(GitReferences, graphene.ObjectType):
    """Arguments passed into the opensha Rupture Generator"""

