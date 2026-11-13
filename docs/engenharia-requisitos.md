# Engenharia de requisitos

[Voltar ao README](../README.md) · [Modelo de domínio](modelo-dominio.md) · [Banco de dados](modelo-banco-dados.md)

Este documento consolida o escopo, os requisitos e as condições de aceitação do Arena Fácil. As definições partem do problema de consulta de horários e organização manual de reservas e das decisões de MVP adotadas pela equipe. Os critérios orientam a verificação da aplicação; a existência de um requisito nesta lista não substitui sua demonstração ou a execução dos testes.

## Problema e objetivo

Reservas organizadas por mensagens, ligações ou anotações dificultam a consulta de disponibilidade e podem gerar registros conflitantes. O objetivo é disponibilizar uma aplicação web na qual o dono ofereça quadras e o cliente consulte horários e realize reservas, com regras explícitas de conflito, cancelamento e preservação do histórico.

O projeto foi definido em contexto acadêmico, a partir da observação do problema, sem parceiro formal ou levantamento com participantes. A solução prioriza código simples, modularização mínima e aplicação de POO explicável pelos integrantes.

## Atores

| Ator          | Necessidades e operações                                                                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cliente       | Cadastrar-se, identificar-se por e-mail, buscar arenas, consultar quadras e horários, reservar, acompanhar o histórico e cancelar suas próprias reservas dentro do prazo. |
| Dono da arena | Cadastrar-se com sua arena, gerenciar suas quadras e consultar os agendamentos da própria arena.                                                                          |

Cada conta possui um perfil. A identificação é funcional e simplificada: conhecer o e-mail ou enviar o id de outro usuário não é impedido por autenticação forte. As restrições de perfil e propriedade não devem ser apresentadas como proteção de identidade para produção.

## Escopo do MVP

Estão incluídos os cadastros, a busca por nome, a gestão de quadras, a disponibilidade, a confirmação de uma reserva por operação, o histórico e o cancelamento pelo cliente. O catálogo contém futevôlei, vôlei e beach tênis, representados por `FUTEVOLEI`, `VOLEI` e `BEACH_TENIS`.

Ficam fora do MVP: senha e recuperação de conta, pagamento, notificações, indicadores gerenciais, cancelamento pelo dono, reservas recorrentes, seleção de várias reservas em uma operação, reativação de quadras e alteração posterior do funcionamento. Não há aplicação mobile nativa, avaliações, lista de espera, promoções ou bloqueios especiais de agenda.

## Organização dos requisitos

Os requisitos foram definidos a partir dos fluxos dos dois perfis e separados em quatro grupos:

- **RF:** operações que a aplicação disponibiliza.
- **RNF:** condições técnicas e de qualidade.
- **RN:** restrições que determinam quando uma operação é válida.
- **CA:** comportamentos observáveis utilizados na aceitação.

Os identificadores permitem relacionar funcionalidades, regras e verificações sem depender de uma correspondência entre classe e tabela.

## Requisitos funcionais

| ID   | Requisito                                                                                                   |
| ---- | ----------------------------------------------------------------------------------------------------------- |
| RF01 | Permitir o cadastro de clientes.                                                                            |
| RF02 | Permitir o cadastro conjunto de um dono e sua única arena.                                                  |
| RF03 | Permitir a identificação por e-mail cadastrado, sem senha.                                                  |
| RF04 | Permitir sair e trocar o usuário identificado na interface.                                                 |
| RF05 | Disponibilizar operações conforme o perfil e validar a propriedade dos registros no back-end.               |
| RF06 | Cadastrar a arena com nome, endereço e intervalo diário de funcionamento.                                   |
| RF07 | Consultar as informações de uma arena.                                                                      |
| RF08 | Listar e pesquisar arenas por trecho do nome, sem diferenciar maiúsculas de minúsculas.                     |
| RF09 | Permitir ao dono cadastrar quadras na própria arena.                                                        |
| RF10 | Consultar quadras, descrição, preço, modalidades e situação.                                                |
| RF11 | Permitir ao dono editar nome, descrição, preço e modalidades de suas quadras, preservando reservas futuras. |
| RF12 | Permitir ao dono excluir ou desativar suas quadras conforme as regras de histórico.                         |
| RF13 | Selecionar pelo menos uma modalidade por quadra a partir do catálogo fixo.                                  |
| RF14 | Consultar horários livres por quadra e data.                                                                |
| RF15 | Filtrar quadras por modalidade.                                                                             |
| RF16 | Exibir as opções livres da arena por quadra, dentro do funcionamento e sem conflito de quadra ou cliente.   |
| RF17 | Criar uma reserva de uma hora por operação, permitindo horas consecutivas em operações independentes.       |
| RF18 | Revalidar disponibilidade, ativação, modalidade, funcionamento e conflitos antes de gravar a reserva.       |
| RF19 | Confirmar automaticamente as reservas válidas.                                                              |
| RF20 | Registrar cliente, quadra, modalidade, início, preço contratado, estado e informações de histórico.         |
| RF21 | Permitir ao cliente consultar suas reservas e histórico, com filtros de situação temporal e data.           |
| RF22 | Permitir ao cliente cancelar suas próprias reservas dentro do prazo.                                        |
| RF23 | Preservar os registros cancelados no histórico.                                                             |
| RF24 | Permitir ao dono consultar os agendamentos da própria arena e filtrar por data, sem cancelá-los.            |

## Requisitos não funcionais

| ID    | Requisito                                                                                                |
| ----- | -------------------------------------------------------------------------------------------------------- |
| RNF01 | Interface acessível por navegador, com layout adaptado a computador e celular.                           |
| RNF02 | Back-end implementado em Python com FastAPI.                                                             |
| RNF03 | Persistência relacional em PostgreSQL, com acesso por Psycopg e SQL parametrizado.                       |
| RNF04 | Front-end em HTML, CSS e JavaScript, sem framework.                                                      |
| RNF05 | Identificação simplificada por e-mail, com limitação de segurança explicitada.                           |
| RNF06 | Validar perfil e propriedade no back-end, reconhecendo a ausência de autenticação forte.                 |
| RNF07 | Proteger a integridade dos dados, inclusive em solicitações simultâneas de reserva.                      |
| RNF08 | Manter código legível, responsabilidades identificáveis e modularização mínima com POO.                  |
| RNF09 | Disponibilizar testes automatizados das regras principais com Pytest.                                    |
| RNF10 | Documentar instalação, configuração, execução e demonstração reproduzível.                               |
| RNF11 | Apresentar mensagens compreensíveis para erros e confirmações.                                           |
| RNF12 | Utilizar Git e GitHub para versionamento, com contribuições e autoria registradas de forma transparente. |

Não foram definidos limites quantitativos de desempenho, disponibilidade ou quantidade de usuários simultâneos. Os testes de concorrência verificam integridade nos cenários implementados; não constituem teste de carga ou garantia de capacidade em produção.

## Regras de negócio

### Usuários e arenas

| ID   | Regra                                                                |
| ---- | -------------------------------------------------------------------- |
| RN01 | Cada usuário possui um único perfil: `CLIENTE` ou `DONO`.            |
| RN02 | Cada dono é cadastrado junto com uma única arena, em uma transação.  |
| RN03 | Cada arena pertence a um único dono.                                 |
| RN04 | Apenas o dono identificado para a arena pode gerenciar suas quadras. |

O e-mail é único entre todos os usuários e é normalizado para minúsculas, sem espaços nas extremidades. O funcionamento é definido no cadastro, vale diariamente e exige abertura anterior ao fechamento no mesmo dia.

### Quadras e modalidades

| ID   | Regra                                                                                |
| ---- | ------------------------------------------------------------------------------------ |
| RN05 | Cada quadra pertence a uma única arena.                                              |
| RN06 | Cada quadra disponibilizada possui pelo menos uma modalidade válida.                 |
| RN07 | As modalidades pertencem ao catálogo predefinido; não existe cadastro independente.  |
| RN08 | As modalidades oferecidas pela arena são derivadas das suas quadras ativas.          |
| RN09 | Não é permitido excluir/desativar quadra com reserva futura confirmada.              |
| RN10 | A retirada de uma quadra deve preservar o histórico dos agendamentos.                |
| RN11 | Alterações de preço valem apenas para novas reservas.                                |
| RN12 | Não é permitido retirar modalidade utilizada em reserva futura confirmada da quadra. |

O preço deve ser positivo e ter até duas casas decimais. Uma quadra sem histórico pode ser apagada; com histórico e sem reserva futura confirmada, é desativada. O estado de ativação não é um campo editável livremente pela API e não há reativação.

### Disponibilidade e reservas

| ID   | Regra                                                                                                                |
| ---- | -------------------------------------------------------------------------------------------------------------------- |
| RN13 | Cada agendamento dura exatamente uma hora.                                                                           |
| RN14 | O início deve estar em hora cheia.                                                                                   |
| RN15 | O início deve ser futuro.                                                                                            |
| RN16 | Todo o intervalo deve caber no funcionamento diário da arena.                                                        |
| RN17 | Uma quadra não pode ter duas reservas confirmadas para o mesmo horário.                                              |
| RN18 | Um cliente não pode ter reservas confirmadas sobrepostas, inclusive entre arenas. Horas consecutivas são permitidas. |
| RN19 | A modalidade deve ser aceita pela quadra.                                                                            |
| RN20 | Reservas válidas são confirmadas imediatamente, sem pagamento ou aprovação.                                          |
| RN21 | O preço vigente é copiado para a reserva e permanece no histórico.                                                   |

A quadra precisa estar ativa. A disponibilidade considera conflitos tanto da quadra quanto do cliente identificado. Como os intervalos são sempre de uma hora e começam em hora cheia, conflitos correspondem ao mesmo instante de início. Datas e horários seguem `America/Fortaleza`.

### Cancelamento

| ID   | Regra                                                                               |
| ---- | ----------------------------------------------------------------------------------- |
| RN22 | Somente o cliente responsável pode cancelar sua reserva; o dono não cancela no MVP. |
| RN23 | O cancelamento exige antecedência mínima de duas horas, inclusive no limite exato.  |
| RN24 | Uma reserva cancelada não pode ser cancelada novamente.                             |
| RN25 | O cancelamento muda o estado e registra a data, sem apagar o histórico.             |
| RN26 | A reserva cancelada deixa de bloquear o horário.                                    |

Os estados são `CONFIRMADO` e `CANCELADO`. Reservas passadas podem permanecer confirmadas; o sistema não exige um estado de conclusão nem registra comparecimento ou recebimento.

## Critérios de aceitação e rastreabilidade

A tabela relaciona os comportamentos esperados às suas definições. O resultado de aceitação deve considerar a execução dos testes e a demonstração da interface.

| ID   | Condição verificável                                                                  | Requisitos relacionados              |
| ---- | ------------------------------------------------------------------------------------- | ------------------------------------ |
| CA01 | Cliente e dono cadastram e entram por e-mail; a interface permite sair.               | RF01–RF04, RN01–RN03.                |
| CA02 | O mesmo dono não possui uma segunda arena.                                            | RF02, RF06, RN02–RN03.               |
| CA03 | Dono cadastra, consulta e edita apenas suas quadras.                                  | RF05, RF09–RF11, RN04–RN07.          |
| CA04 | Retirada sem reserva futura preserva o histórico quando existente.                    | RF12, RN09–RN10.                     |
| CA05 | Cadastro e edição exigem modalidade válida e preço positivo.                          | RF10–RF13, RN06–RN07.                |
| CA06 | Cliente busca arena por nome, filtra modalidade e consulta horários por data.         | RF07–RF08, RF14–RF16.                |
| CA07 | Reserva válida fica confirmada com os dados e preço contratados.                      | RF17–RF20, RN13–RN16, RN19–RN21.     |
| CA08 | Conflitos de quadra ou cliente são rejeitados, inclusive em solicitações simultâneas. | RF18, RN17–RN18, RNF07.              |
| CA09 | O cliente consegue reservar horas consecutivas em operações separadas.                | RF17, RN18.                          |
| CA10 | Passado, hora fracionada, funcionamento inválido e quadra inativa impedem reserva.    | RF18, RN14–RN16.                     |
| CA11 | Apenas o cliente responsável cancela com duas horas ou mais de antecedência.          | RF22, RN22–RN24.                     |
| CA12 | Cancelar libera o horário e mantém o registro no histórico.                           | RF21–RF23, RN25–RN26.                |
| CA13 | Dono consulta apenas as reservas da própria arena.                                    | RF05, RF24, RN04.                    |
| CA14 | Edição preserva o preço contratado e não remove modalidade com reserva futura.        | RF11, RN11–RN12, RN21.               |
| CA15 | Dados continuam disponíveis após nova inicialização da API com o mesmo banco.         | RF20–RF21, RNF03.                    |
| CA16 | A suíte automatizada executa com PostgreSQL e sem falhas.                             | RNF07, RNF09.                        |
| CA17 | O fluxo completo é demonstrado com interface, API e banco integrados.                 | RF01–RF24, RNF01–RNF04, RNF10–RNF11. |

## Verificações implementadas

Os arquivos de teste são [test_quadras.py](../tests/test_quadras.py) e [test_agendamentos.py](../tests/test_agendamentos.py). As instruções de execução estão no [README](../README.md#executar-os-testes).

| Grupo                    | Exemplos de evidência automatizada                                                                                                                                      |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cadastro e identificação | `test_cadastro_entrada_email_unico_e_arena`, `test_cadastro_invalido_nao_cria_dono`, `test_segunda_arena_bloqueada_no_banco`.                                           |
| Busca e propriedade      | `test_busca_apenas_nome_e_literal`, `test_propriedade_e_perfis`, `test_conflito_entre_arenas_e_visibilidade_do_dono`.                                                   |
| Quadras e modalidades    | `test_validacao_quadra`, `test_editar_e_excluir_sem_historico`, `test_modalidade_e_perfil_na_reserva`.                                                                  |
| Horários e conflitos     | `test_horarios_invalidos`, `test_limites_funcionamento_e_offset`, `test_conflitos_e_horas_consecutivas`.                                                                |
| Concorrência             | `test_duas_requisicoes_simultaneas`, `test_reserva_simultanea_com_alteracao_quadra`, `test_indices_protegem_banco`.                                                     |
| Cancelamento             | `test_limite_duas_horas`, `test_cancelamento_propriedade_dono_e_repeticao`, `test_fluxo_completo_cancelar_libera_e_preserva`.                                           |
| Histórico e persistência | `test_edicao_preserva_modalidade_e_preco`, `test_desativacao_historico_e_quadra_inativa`, `test_desativacao_com_reserva_passada`, `test_persistencia_apos_reabrir_api`. |
| Integração HTTP          | `test_interface_e_saude` verifica os arquivos servidos e a conexão da API com o banco.                                                                                  |

As verificações da interface complementam os testes HTTP: eventos de formulários e seleções, navegação entre perfis, atualização de horários, resumo da reserva, filtros do histórico e apresentação de erros devem ser conferidos em navegador. A aprovação dos testes HTTP não comprova sozinha legibilidade, responsividade ou usabilidade.

O workflow de GitHub Actions está configurado no repositório. Seu resultado e a contribuição dos integrantes devem ser demonstrados pelo histórico real de execuções e commits, sem inferir essas evidências a partir da existência dos arquivos.

## Decisões técnicas relacionadas

- A interface e a API são servidas pelo mesmo processo FastAPI.
- A identificação ativa usa `sessionStorage` e o cabeçalho `X-Usuario-Id`.
- O banco guarda horários locais de Fortaleza em `TIMESTAMP` sem offset; entradas com offset são convertidas.
- Os índices únicos parciais complementam as verificações da aplicação e as transações de reserva.
- A edição e a exclusão de quadras usam a mesma coordenação por bloqueio de registro da reserva.
- O esquema é inicializado pela API, sem ferramenta de migrações.

A organização das classes é apresentada no [Modelo de domínio](modelo-dominio.md). As tabelas, restrições e limites das garantias do SQL estão detalhados no [Modelo do banco de dados](modelo-banco-dados.md).
