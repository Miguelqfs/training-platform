# Glossário

Os termos abaixo devem manter o mesmo sentido na visão, nas especificações e nos diagramas. Os conceitos de treino descrevem a visão futura; somente os conceitos de usuário estão implementados nesta entrega.

| Termo | Definição | Sinônimos a evitar | Exemplo |
| --- | --- | --- | --- |
| Administrador | Pessoa cadastrada com papel `admin`, destinada a operar a plataforma. O papel ainda não concede permissões na API atual. | gestor, operador | Cadastro com `role: admin`. |
| Agente de IA | Componente futuro que auxiliará o trabalho com os treinos. Não é um usuário cadastrado. | treinador humano | Treinador IA planejado. |
| Aluno | Pessoa cadastrada com papel `student`, público principal do acompanhamento de treinos. | cliente, atleta | Cadastro com `role: student`. |
| Cadastro de usuário | Registro de login, e-mail, senha e papel na plataforma. | inscrição | Operação `POST /users/`. |
| Login | Identificador único do usuário, com até 12 caracteres, não vazio e sem números. | username, nome de usuário | `maria`. |
| Papel | Tipo atribuído ao usuário: aluno ou administrador. | perfil, permissão | `student` ou `admin`. |
| Persistência | Meio usado para armazenar usuários: coleção em RAM ou banco SQLite. | banco, memória | `USER_STORAGE=sqlite`. |
| Preferência de treino | Informação futura sobre escolhas do aluno relacionadas ao treino. Ainda não há campos definidos para ela. | configuração | Preferências informadas pelo aluno. |
| Senha | Credencial de cadastro sujeita à política IAM padrão; seu valor original não é armazenado. | password | Nunca aparece na resposta da API. |
| Treino | Conjunto de atividades físicas que o aluno pretende acompanhar no produto futuro. A estrutura ainda não foi especificada. | rotina, ficha | Treino acompanhado pelo aluno. |
| Usuário | Pessoa cadastrada na plataforma, identificada por ID, login, e-mail e papel. | conta | Aluno ou administrador. |
