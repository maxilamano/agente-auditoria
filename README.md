
# Agente auditoria

Este es un proyecto simple de IA que permite auditar codigos dentro de repositorios de github.


## Instalación

Para utilizar este repositorio necesitas python. Este proyecto solo se ha testeado usando 3.13.3, cualquier versión superior a esta deberia funcionar igualmente.

Con esto también necesitas multiples paquetes de python, los puedes instalar con windows PowerShell o el terminal de linux usando:

```bash
  python -m pip install streamlit langchain langchain-community pylance langchain-chroma gitpython requests
```


También necesitarás OLLAMA para gestionar el modelo de IA, lo puedes instalar usando el siguiente comando:

windows(powershell):
```bash
irm https://ollama.com/install.ps1 | iex
```
linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```


Teniendo OLLAMA, montamos el modelo usando:

```bash
ollama run qwen2.5-coder:7b
```


## FAQ

#### ¿Puedo redistribuir este programa?

No.

#### ¿Que?

So.
