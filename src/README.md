# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se e remover estudantes de atividades (com autenticação)
- Login de professores para ações administrativas
- Exibir anúncios ativos no topo da interface
- Gerenciar anúncios (criar, editar e excluir) para usuários autenticados

## Como começar

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| POST   | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove estudante de uma atividade                                    |
| POST   | `/auth/login?username=...&password=...`                          | Realiza login de professor                                           |
| GET    | `/auth/check-session?username=...`                               | Valida sessão de usuário                                             |
| GET    | `/announcements/active`                                           | Lista anúncios ativos para exibição pública                          |
| GET    | `/announcements?teacher_username=...`                            | Lista todos os anúncios para gerenciamento (autenticado)             |
| POST   | `/announcements?teacher_username=...`                            | Cria anúncio com data de expiração obrigatória                       |
| PUT    | `/announcements/{announcement_id}?teacher_username=...`          | Atualiza anúncio existente                                            |
| DELETE | `/announcements/{announcement_id}?teacher_username=...`          | Exclui anúncio                                                       |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Os dados são armazenados no MongoDB local (`mergington_high`) e inicializados com dados de exemplo quando a base estiver vazia.
