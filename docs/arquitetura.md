# Arquitetura planejada

Na Sprint 1, apenas a API de usuários é executável. O código fica em `app/`: `routers/` e `schemas.py` formam a fronteira HTTP; `users/service.py` controla o cadastro, a listagem e a coleção em RAM; `users/domain.py` define a entidade.

O produto futuro terá um aplicativo mobile consumindo a API. Um agente de IA exercerá a função de treinador por meio de ferramentas controladas pelo servidor para consultar dados autorizados e criar ou editar treinos. Esses componentes ganharão pastas próprias quando forem implementados. O agente não será cadastrado como aluno ou administrador.
