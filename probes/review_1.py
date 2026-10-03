"""Regression probe: SDK malformed allowed destinations must raise InputError."""
from splitleak import InputError, load


def run():
    for allowed in [[{}], [[]], [True], [1, "train"]]:
        try:
            load({"splits": ["train", "test"], "samples": [
                {"id": "A", "split": "train", "allowed_splits": allowed}]})
        except InputError:
            pass
        except Exception as error:
            raise AssertionError(f"expected InputError, got {type(error).__name__}") from None
        else:
            raise AssertionError("malformed destination accepted")
    print("review_1: PASS (4 malformed SDK destinations rejected as InputError)")


if __name__ == "__main__":
    run()
