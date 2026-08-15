import pytest

from app.normalization.entity_normalizer import EntityNormalizer


@pytest.fixture
def normalizer():
    return EntityNormalizer()


def test_organization_variants(normalizer):
    assert normalizer.normalize_organization("Google Inc") == "google"
    assert normalizer.normalize_organization("GOOGLE") == "google"

    assert (
        normalizer.normalize_organization("Microsoft Corporation")
        == "microsoft"
    )

    assert (
        normalizer.normalize_organization("International Business Machines")
        == "ibm"
    )


def test_company_aliases(normalizer):
    assert normalizer.normalize_organization("Facebook") == "meta"
    assert normalizer.normalize_organization("Meta Platforms") == "meta"


def test_react_variants(normalizer):
    assert normalizer.normalize_technology("ReactJS") == "react"
    assert normalizer.normalize_technology("React.js") == "react"
    assert normalizer.normalize_technology("React JS") == "react"


def test_database_variants(normalizer):
    assert normalizer.normalize_technology("Postgres") == "postgresql"
    assert normalizer.normalize_technology("PostgreSQL") == "postgresql"

    assert normalizer.normalize_technology("Mongo DB") == "mongodb"
    assert normalizer.normalize_technology("MongoDB") == "mongodb"


def test_cloud_variants(normalizer):
    assert normalizer.normalize_technology("AWS") == "aws"
    assert (
        normalizer.normalize_technology("Amazon Web Services")
        == "aws"
    )

    assert normalizer.normalize_technology("GCP") == "gcp"
    assert (
        normalizer.normalize_technology("Google Cloud Platform")
        == "gcp"
    )

    assert normalizer.normalize_technology("Microsoft Azure") == "azure"


def test_kubernetes_variants(normalizer):
    assert normalizer.normalize_technology("Kubernetes") == "kubernetes"
    assert normalizer.normalize_technology("K8s") == "kubernetes"


def test_unknown_entity_is_preserved(normalizer):
    assert (
        normalizer.normalize_technology("LangChain")
        == "langchain"
    )

    assert (
        normalizer.normalize_organization("Acme Corporation")
        == "acme corporation"
    )


def test_multiple_organizations(normalizer):
    organizations = [
        "Google",
        "Google Inc",
        "Microsoft",
        "MICROSOFT",
    ]

    result = normalizer.normalize_organizations(organizations)

    assert result == [
        "google",
        "microsoft",
    ]


def test_multiple_technologies(normalizer):
    technologies = [
        "ReactJS",
        "React.js",
        "AWS",
        "Amazon Web Services",
        "K8s",
        "Kubernetes",
    ]

    result = normalizer.normalize_technologies(technologies)

    assert result == [
        "react",
        "aws",
        "kubernetes",
    ]


def test_empty_entity(normalizer):
    assert normalizer.normalize_technology("") == ""


def test_whitespace(normalizer):
    assert (
        normalizer.normalize_organization("  Google Inc  ")
        == "google"
    )