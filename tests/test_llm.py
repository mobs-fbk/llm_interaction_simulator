import pytest
from httpx import ConnectError
from ollama import ResponseError

from llm_simulator.general.llm import LLM


def ollama_pull_response(model_name: str) -> None:
    if model_name == "falcon:latest":
        return None
    elif model_name == "stopped_ollama":
        raise ConnectError(
            "No connection could be made because the target machine actively refused it"
        )
    elif model_name == "invalid_model":
        raise ResponseError(error="pull model manifest: file does not exist")


@pytest.fixture
def mock_ollama(mocker) -> None:
    model_examples = {
        "models": [
            {
                "name": "falcon:latest",
                "model": "falcon:latest",
                "modified_at": "2024-04-29T11:21:16.1425078+02:00",
                "size": 4210994570,
                "digest": "4280f7257e73108cddb43de89eb9fa28350a21aaaf997b5935719f9de0281563",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "falcon",
                    "families": None,
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0",
                },
            }
        ]
    }
    mocker.patch("ollama.list", return_value=model_examples)
    mocker.patch(
        "ollama.pull",
        side_effect=ollama_pull_response,
    )
    mocker.patch("ollama.create", return_value=None)


@pytest.mark.usefixtures("mock_ollama")
def test_llm_initialization_valid_model() -> None:
    llm = LLM(model="falcon:latest")
    # Add assertions to check if the initialization went as expected
    assert llm.model == "falcon:latest".lower()


@pytest.mark.usefixtures("mock_ollama")
def test_llm_initialization_invalid_model() -> None:
    with pytest.raises(Exception) as excinfo:
        LLM(model="invalid_model")
    print(excinfo)
    assert excinfo.type == ResponseError


@pytest.mark.usefixtures("mock_ollama")
def test_ollama_not_working() -> None:
    with pytest.raises(Exception) as excinfo:
        LLM(model="stopped_ollama")
    assert excinfo.type == ConnectError
