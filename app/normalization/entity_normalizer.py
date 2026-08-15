from typing import Iterable

from app.normalization.normalizer_utils import normalize_text


class EntityNormalizer:
    """
    Deterministically normalizes organizations and technology-related
    entities into canonical representations.
    """

    ORGANIZATION_ALIASES = {
        "google inc": "google",
        "google llc": "google",
        "google": "google",

        "microsoft corporation": "microsoft",
        "microsoft corp": "microsoft",
        "microsoft": "microsoft",

        "amazon": "amazon",
        "amazon inc": "amazon",
        "amazon.com": "amazon",

        "meta platforms": "meta",
        "meta platforms inc": "meta",
        "facebook": "meta",
        "facebook inc": "meta",

        "apple inc": "apple",
        "apple": "apple",

        "ibm corporation": "ibm",
        "international business machines": "ibm",
        "ibm": "ibm",
    }

    TECHNOLOGY_ALIASES = {
        # Python
        "python": "python",
        "python3": "python",

        # Java
        "java": "java",
        "java se": "java",

        # JavaScript
        "javascript": "javascript",
        "java script": "javascript",
        "js": "javascript",

        # TypeScript
        "typescript": "typescript",
        "type script": "typescript",
        "ts": "typescript",

        # React
        "react": "react",
        "reactjs": "react",
        "react.js": "react",
        "react js": "react",

        # Angular
        "angular": "angular",
        "angularjs": "angular",
        "angular.js": "angular",

        # Vue
        "vue": "vue",
        "vuejs": "vue",
        "vue.js": "vue",

        # Node
        "node": "node.js",
        "nodejs": "node.js",
        "node.js": "node.js",
        "node js": "node.js",

        # PyTorch
        "pytorch": "pytorch",
        "py torch": "pytorch",
        "py-torch": "pytorch",

        # TensorFlow
        "tensorflow": "tensorflow",
        "tensor flow": "tensorflow",
        "tf": "tensorflow",

        # Databases
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "postgre sql": "postgresql",

        "mysql": "mysql",

        "mongo": "mongodb",
        "mongodb": "mongodb",
        "mongo db": "mongodb",

        "mssql": "sql server",
        "ms sql": "sql server",
        "sql server": "sql server",

        # Cloud
        "aws": "aws",
        "amazon web services": "aws",

        "gcp": "gcp",
        "google cloud": "gcp",
        "google cloud platform": "gcp",

        "azure": "azure",
        "microsoft azure": "azure",

        # Containers
        "docker": "docker",

        "kubernetes": "kubernetes",
        "k8s": "kubernetes",

        # Version control
        "git": "git",

        "github": "github",
        "git hub": "github",

        "gitlab": "gitlab",
        "git lab": "gitlab",

        # APIs
        "rest": "rest",
        "rest api": "rest",

        "restful api": "rest",

        "graphql": "graphql",
        "graph ql": "graphql",
    }

    def normalize_organization(self, organization: str) -> str:
        """
        Normalize a single organization name.
        """

        normalized = normalize_text(organization)

        return self.ORGANIZATION_ALIASES.get(
            normalized,
            normalized,
        )

    def normalize_technology(self, technology: str) -> str:
        """
        Normalize a single technology/entity.
        """

        normalized = normalize_text(technology)

        return self.TECHNOLOGY_ALIASES.get(
            normalized,
            normalized,
        )

    def normalize_organizations(
        self,
        organizations: Iterable[str],
    ) -> list[str]:
        """
        Normalize multiple organizations and remove duplicates.
        """

        result = []
        seen = set()

        for organization in organizations:
            canonical = self.normalize_organization(organization)

            if canonical and canonical not in seen:
                result.append(canonical)
                seen.add(canonical)

        return result

    def normalize_technologies(
        self,
        technologies: Iterable[str],
    ) -> list[str]:
        """
        Normalize multiple technologies and remove duplicates.
        """

        result = []
        seen = set()

        for technology in technologies:
            canonical = self.normalize_technology(technology)

            if canonical and canonical not in seen:
                result.append(canonical)
                seen.add(canonical)

        return result