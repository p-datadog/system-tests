import requests

from utils import features


def get_known_features():
    """ return an object feature_id -> attribute name in features decorator """
    result = {}

    for attr in dir(features):
        if attr.startswith("__"):
            continue

        def obj():
            pass

        obj = getattr(features, attr)(obj)

        if hasattr(obj, "pytestmark"):
            result[obj.pytestmark[0].kwargs["feature_id"]] = attr

    return result


def _main():
    known_features = get_known_features()

    data = requests.get("https://dd-feature-parity.azurewebsites.net/Import/Features", timeout=10).json()
    for feature in data:
        feature_id = feature["id"]
        if feature_id not in known_features:
            docstring = f"""
        {feature['name']}

        https://feature-parity.us1.prod.dog/#/?feature={feature_id}"""
            print(
                f"""
    @staticmethod
    def {feature['codeSafeName'].lower()}(test_object):
        ""\"{docstring}
        ""\"
        pytest.mark.features(feature_id={feature_id})(test_object)
        return test_object
"""
            )


if __name__ == "__main__":
    _main()
