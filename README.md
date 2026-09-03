# ChamaPro Serviços  
   
> Marketplace de serviços que conecta clientes a profissionais de forma simples, organizada e segura.  
   
---  
   
## 📌 Sobre o projeto  
   
O **ChamaPro Serviços** é uma plataforma de marketplace desenvolvida em Django para conectar pessoas que precisam de serviços a profissionais que oferecem esses serviços.  
   
O funcionamento da plataforma é baseado em **solicitações, orçamentos e contratação**.  
   
O cliente não escolhe diretamente um profissional ao entrar na plataforma.  
   
O fluxo principal é:  
   
**Categoria → Solicitação → Orçamentos → Escolha → Contratação → Pagamento → Execução → Conclusão**  
   
Dessa forma, uma mesma solicitação pode receber propostas de diferentes profissionais, permitindo ao cliente comparar valores, prazos e condições antes de contratar.  
   
---  
   
# 🎯 Objetivos  
   
O projeto tem como objetivos:  
   
- conectar clientes e profissionais;  
- facilitar a solicitação de serviços;  
- permitir que vários profissionais apresentem propostas;  
- permitir comparação de orçamentos;  
- facilitar a contratação;  
- disponibilizar pagamentos online;  
- controlar o ciclo da contratação;  
- controlar comissões da plataforma;  
- oferecer ferramentas administrativas;  
- futuramente disponibilizar avaliação e reputação dos profissionais.  
   
---  
   
# 👥 Usuários da plataforma  
   
O sistema trabalha principalmente com três perfis.  
   
## Cliente  
   
Pode:  
   
- criar solicitações;  
- informar categoria;  
- descrever a necessidade;  
- adicionar fotos;  
- informar localização;  
- informar data desejada;  
- receber orçamentos;  
- comparar propostas;  
- contratar um profissional;  
- realizar pagamentos;  
- cancelar solicitações ou contratações quando permitido;  
- acompanhar o serviço.  
   
## Profissional  
   
Pode:  
   
- realizar cadastro profissional;  
- cadastrar serviços;  
- visualizar solicitações disponíveis;  
- enviar orçamentos;  
- acompanhar seus orçamentos;  
- acompanhar serviços contratados;  
- executar os serviços;  
- acompanhar o fluxo de recebimento.  
   
## Administrador  
   
Pode:  
   
- administrar a plataforma;  
- acompanhar informações administrativas;  
- consultar relatórios;  
- acompanhar volume negociado;  
- acompanhar comissões;  
- acompanhar repasses aos profissionais.  
   
---  
   
# 🔄 Fluxo principal  
   
```text  
                         CHAMAPRO SERVIÇOS  
                                │  
                ┌───────────────┴───────────────┐  
                │                               │  
             CLIENTE                       PROFISSIONAL  
                │                               │  
                ▼                               ▼  
       Escolhe categoria                  Cadastra serviços  
                │                               │  
                ▼                               │  
       Cria solicitação                         │  
                │                               │  
                └───────────────┬───────────────┘  
                                ▼  
                     SOLICITAÇÃO DISPONÍVEL  
                                │  
                                ▼  
                      PROFISSIONAIS ANALISAM  
                                │  
                                ▼  
                       ENVIAM ORÇAMENTOS  
                                │  
                                ▼  
                       CLIENTE ANALISA  
                                │  
                                ▼  
                     ACEITA UM ORÇAMENTO  
                                │  
                                ▼  
                           CONTRATAÇÃO  
                                │  
                                ▼  
                            PAGAMENTO  
                                │  
                   ┌────────────┴────────────┐  
                   │                         │  
                  PIX                      CARTÃO  
                   │                         │  
                   └────────────┬────────────┘  
                                ▼  
                       SERVIÇO EM EXECUÇÃO  
                                │  
                                ▼  
                       SERVIÇO CONCLUÍDO  
                                │  
                                ▼  
                    COMISSÃO + REPASSE  
# **🧭 Fluxo do cliente**  
Cadastro  
   ↓  
Login  
   ↓  
Minha conta  
   ↓  
Escolha da categoria  
   ↓  
Nova solicitação  
   ↓  
Descrição  
   ↓  
Localização  
   ↓  
Data desejada  
   ↓  
Fotos  
   ↓  
Publicação  
   ↓  
Recebimento de orçamentos  
   ↓  
Análise das propostas  
   ↓  
Aceitação  
   ↓  
Contratação  
   ↓  
Pagamento  
   ↓  
Execução do serviço  
   ↓  
Conclusão  
# **🧰 Fluxo do profissional**  
Cadastro profissional  
        ↓  
Envio do cadastro  
        ↓  
Cadastro dos serviços  
        ↓  
Solicitações disponíveis  
        ↓  
Análise  
        ↓  
Envio de orçamento  
        ↓  
Aguardar decisão do cliente  
        ↓  
Cliente aceita  
        ↓  
Contratação  
        ↓  
Execução  
        ↓  
Conclusão  
        ↓  
Recebimento  
# **💰 Fluxo financeiro**  
O ChamaPro utiliza o **Mercado Pago** como intermediador de pagamentos.  
Os meios de pagamento atualmente contemplados são:  
- PIX  
- Cartão  
Fluxo:  
Cliente  
   ↓  
Contratação  
   ↓  
Pagamento  
   ↓  
Mercado Pago  
   ↓  
Pagamento aprovado  
   ↓  
Serviço  
   ↓  
Serviço concluído  
   ↓  
Valor bruto  
   ├──────────────→ Comissão ChamaPro  
   │  
   └──────────────→ Valor profissional  
# **🔁 Fluxo de cancelamento**  
## **Cancelamento da solicitação**  
Antes de cancelar, o sistema deve verificar se o estado atual permite o cancelamento.  
Solicitação  
     ↓  
Verificar status  
     ↓  
Pode cancelar?  
   ↙       ↘  
 SIM       NÃO  
  ↓         ↓  
Cancela    Mensagem  
## **Cancelamento da contratação**  
Contratação  
     ↓  
Verificar status  
     ↓  
Pode cancelar?  
     ↓  
Cancelar contratação  
     ↓  
Existe pagamento?  
   ↙       ↘  
 NÃO       SIM  
  ↓         ↓  
Cancelar   Pagamento aprovado?  
pagamento       ↓  
               SIM  
                ↓  
       Solicitar estorno  
                ↓  
          Mercado Pago  
Quando existe pagamento aprovado, o sistema tenta realizar o estorno através da integração com o Mercado Pago.  
# **📊 Estados da solicitação**  
A solicitação possui atualmente os seguintes estados:  
ABERTA  
RECEBENDO_ORCAMENTOS  
ORCAMENTO_ACEITO  
EM_EXECUCAO  
AGUARDANDO_PAGAMENTO  
CONCLUIDA  
CANCELADA  
Fluxo principal:  
ABERTA  
   ↓  
RECEBENDO_ORCAMENTOS  
   ↓  
ORCAMENTO_ACEITO  
   ↓  
EM_EXECUCAO  
   ↓  
AGUARDANDO_PAGAMENTO  
   ↓  
CONCLUIDA  
O cancelamento depende do estado atual e das regras de negócio.  
# **🏗️ Arquitetura do projeto**  
Estrutura conceitual:  
ChamaPro  
│  
├── usuarios  
│  
├── servicos  
│  
├── solicitacoes  
│  
├── categorias  
│  
├── relatorios_administrativos  
│  
├── templates  
│  
├── static  
│  
└── media  
# **📦 Aplicações Django**  
## **usuarios**  
Responsável pelos usuários da plataforma e pelos perfis de cliente e profissional.  
## **categorias**  
Responsável pelas categorias de serviços.  
Exemplos:  
- Eletricista  
- Encanador  
- Pintor  
- Pedreiro  
- etc.  
A categoria representa o tipo de necessidade do cliente.  
## **servicos**  
Responsável pelos serviços oferecidos pelos profissionais.  
Cada serviço está associado a:  
- profissional;  
- categoria;  
- nome;  
- descrição;  
- preço de referência;  
- status;  
- datas de cadastro/atualização.  
## **solicitacoes**  
É um dos principais módulos do sistema.  
Responsável por:  
- solicitações;  
- fotos;  
- orçamentos;  
- contratação;  
- pagamento;  
- cancelamento;  
- integração com Mercado Pago;  
- webhook.  
## **relatorios_administrativos**  
Responsável pelas funcionalidades administrativas e relatórios.  
Atualmente inclui:  
- dashboard administrativo;  
- extrato de comissões.  
# **🔗 Relacionamentos principais**  
                    USUÁRIO  
                   /       \  
                  /         \  
             CLIENTE      PROFISSIONAL  
                │               │  
                │               │  
                ▼               ▼  
          SOLICITAÇÃO        SERVIÇO  
                │               │  
                │               │  
                └───────┬───────┘  
                        │  
                   CATEGORIA  
                        │  
                        ▼  
                   ORÇAMENTOS  
                        │  
                        ▼  
                   CONTRATAÇÃO  
                        │  
                        ▼  
                    PAGAMENTO  
# **⚠️ Decisão arquitetural importante**  
A Solicitacao **não possui uma relação direta com ** **Servico**.  
Essa decisão é intencional.  
Uma solicitação representa uma **necessidade do cliente**.  
Um serviço representa uma **oferta de um profissional**.  
A categoria funciona como elo conceitual:  
Cliente  
   ↓  
Necessidade  
   ↓  
Categoria  
   ↓  
Serviços compatíveis  
   ↓  
Profissionais  
   ↓  
Orçamentos  
Isso permite que vários profissionais possam responder à mesma solicitação.  
# **📝 Solicitações**  
Uma solicitação possui informações como:  
- cliente;  
- categoria;  
- título;  
- descrição;  
- cidade;  
- estado;  
- endereço;  
- número;  
- bairro;  
- CEP;  
- data desejada;  
- status;  
- data de criação;  
- data de atualização.  
Também pode possuir fotos.  
# **🏷️ Categoria e título da solicitação**  
Quando uma categoria é escolhida, o título pode ser preenchido automaticamente através da descrição da categoria.  
Exemplo:  
Categoria:  
Eletricista  
   
Descrição:  
Instalação e manutenção elétrica residencial ou predial  
   
Título:  
Instalação e manutenção elétrica residencial ou predial  
O título é somente leitura no formulário.  
# **💬 Orçamentos**  
Uma solicitação pode receber diversos orçamentos.  
Cada orçamento pode apresentar:  
- profissional;  
- valor;  
- descrição;  
- prazo de execução;  
- validade;  
- data.  
O cliente escolhe a proposta que considera mais adequada.  
Solicitação  
    │  
    ├── Orçamento 1  
    ├── Orçamento 2  
    ├── Orçamento 3  
    └── Orçamento N  
             ↓  
       Cliente escolhe  
             ↓  
        Contratação  
# **🤝 Contratação**  
A contratação ocorre depois que o cliente aceita um orçamento.  
Orçamento  
    ↓  
Aceitação  
    ↓  
Contratação  
    ↓  
Pagamento  
    ↓  
Execução  
    ↓  
Conclusão  
# **💳 Mercado Pago**  
A plataforma possui integração com o Mercado Pago.  
Funcionalidades contempladas:  
- pagamento PIX;  
- pagamento por cartão;  
- Payment Brick;  
- processamento de pagamento;  
- consulta de status;  
- webhook;  
- tentativa de estorno em cancelamentos de pagamentos aprovados.  
A integração financeira deve ser considerada uma área crítica do projeto.  
# **🖥️ Principais URLs**  
As principais áreas do projeto são:  
/usuarios/  
/servicos/  
/solicitacoes/  
/categorias/  
/admin-relatorios/  
Dentro de solicitacoes, existem funcionalidades para:  
Nova solicitação  
Detalhe  
Cancelar solicitação  
Orçamentos  
Aceitar orçamento  
Contratar orçamento  
Pagamento  
Processar pagamento  
Pagamento com cartão  
Cancelar contratação  
Solicitações disponíveis  
Novo orçamento  
Meus orçamentos  
Meus serviços contratados  
Webhook Mercado Pago  
# **🎨 Identidade visual**  
O projeto utiliza a identidade visual **ChamaPro**.  
Principais características:  
- laranja como cor principal;  
- Tailwind CSS;  
- cards arredondados;  
- sombras suaves;  
- suporte a dark mode;  
- badges;  
- ícones;  
- botões de ação destacados;  
- layout responsivo.  
A implementação visual deve utilizar preferencialmente as classes padrão do Tailwind:  
orange-50  
orange-100  
orange-500  
orange-600  
orange-700  
em vez de depender de classes customizadas que não estejam presentes na configuração compilada do Tailwind.  
# **📱 Telas desenvolvidas**  
## **Cliente**  
- Home  
- Login  
- Minha conta  
- Nova solicitação  
- Detalhe da solicitação  
- Orçamentos  
- Meus orçamentos  
- Pagamento  
- Pagamento PIX  
- Processamento de pagamento  
- Recuperação de senha  
## **Profissional**  
- Cadastro profissional  
- Solicitações disponíveis  
- Novo orçamento  
- Meus orçamentos  
- Serviços contratados  
## **Administração**  
- Dashboard administrativo  
- Extrato de comissões  
# **📈 Relatórios administrativos**  
O sistema possui relatório de comissões.  
O relatório permite selecionar:  
- mês;  
- ano.  
São apresentados:  
- volume negociado;  
- comissão da plataforma;  
- repasse aos profissionais;  
- detalhamento das contratações.  
Conceito:  
VALOR BRUTO  
     │  
     ├── COMISSÃO CHAMAPRO  
     │  
     └── VALOR PROFISSIONAL  
# **🔐 Segurança**  
Antes da publicação em produção, deverão ser revisados:  
- autenticação;  
- autorização;  
- permissões;  
- CSRF;  
- validação de dados;  
- proteção das views;  
- variáveis de ambiente;  
- credenciais;  
- configuração do banco;  
- HTTPS;  
- logs;  
- auditoria;  
- backups.  
# **🧪 Testes**  
O fluxo principal deverá ser validado ponta a ponta.  
## **Cliente**  
-  Cadastro   
-  Login   
-  Criar solicitação   
-  Adicionar fotos   
-  Visualizar solicitação   
-  Receber orçamentos   
-  Comparar orçamentos   
-  Aceitar orçamento   
-  Contratar   
-  Pagar   
-  Acompanhar serviço   
-  Cancelar quando permitido   
## **Profissional**  
-  Cadastro   
-  Cadastro de serviço   
-  Visualizar solicitações   
-  Enviar orçamento   
-  Acompanhar orçamento   
-  Acompanhar contratação   
-  Concluir serviço   
## **Financeiro**  
-  PIX   
-  Cartão   
-  Pagamento aprovado   
-  Pagamento recusado   
-  Pagamento pendente   
-  Webhook   
-  Cancelamento   
-  Estorno   
-  Comissão   
-  Repasse   
## **Administração**  
-  Dashboard   
-  Relatório de comissões   
-  Filtros   
-  Controle de acesso   
# **🚧 Situação atual**  
| | |  
|-|-|  
| **Módulo** | **Situação** |   
| Usuários | ✅ Implementado |   
| Clientes | ✅ Implementado |   
| Profissionais | ✅ Implementado |   
| Categorias | ✅ Implementado |   
| Serviços | ✅ Implementado |   
| Solicitações | ✅ Implementado |   
| Fotos | ✅ Implementado |   
| Orçamentos | ✅ Implementado |   
| Contratação | ✅ Implementado |   
| PIX | 🔎 Validar ponta a ponta |   
| Cartão | 🔎 Validar ponta a ponta |   
| Mercado Pago | 🔎 Validar ponta a ponta |   
| Webhook | 🔎 Validar |   
| Cancelamento | ✅ Implementado |   
| Estorno | 🔎 Validar |   
| Comissões | ✅ Implementado |   
| Dashboard administrativo | ✅ Implementado |   
| Avaliações | ⏳ Planejado |   
| Notificações | ⏳ Planejado |   
| Aplicativo mobile | ⏳ Futuro |   
# **🗺️ Roadmap**  
## **Fase 1 — Estabilização**  
Prioridade atual.  
- validar fluxo completo;  
- testar contratação;  
- testar pagamentos;  
- testar webhook;  
- testar cancelamentos;  
- testar estorno;  
- revisar transições de status;  
- revisar permissões.  
## **Fase 2 — Experiência do usuário**  
- aprimorar dashboard do cliente;  
- aprimorar dashboard do profissional;  
- melhorar acompanhamento da contratação;  
- melhorar mensagens;  
- melhorar feedback visual;  
- finalizar padronização das telas.  
## **Fase 3 — Avaliações**  
Implementar:  
Serviço concluído  
       ↓  
Cliente avalia  
       ↓  
Nota de 1 a 5  
       ↓  
Comentário  
       ↓  
Reputação do profissional  
Possíveis indicadores:  
- nota média;  
- quantidade de avaliações;  
- avaliações recentes;  
- histórico.  
## **Fase 4 — Notificações**  
Possíveis eventos:  
Nova solicitação  
       ↓  
Profissional recebe notificação  
   
Novo orçamento  
       ↓  
Cliente recebe notificação  
   
Orçamento aceito  
       ↓  
Profissional recebe notificação  
   
Pagamento  
       ↓  
Cliente + profissional recebem notificação  
   
Serviço concluído  
       ↓  
Cliente recebe notificação  
## **Fase 5 — Segurança e produção**  
- configuração definitiva do ambiente;  
- HTTPS;  
- banco de produção;  
- backups;  
- logs;  
- auditoria;  
- monitoramento;  
- tratamento de erros;  
- testes de carga;  
- recuperação de falhas.  
## **Fase 6 — Aplicativo mobile**  
Após a estabilização da plataforma web.  
A estratégia prevista é manter o backend Django e criar uma camada mobile consumindo a infraestrutura do sistema.  
# **🧠 Decisões de arquitetura**  
## **1. Categoria é o ponto de entrada**  
O cliente começa pela categoria que representa sua necessidade.  
## **2. Não existe contratação direta pela Home**  
A Home apresenta possibilidades de serviços/categorias.  
A contratação acontece posteriormente, através de um orçamento.  
## **3. Uma solicitação pode receber vários orçamentos**  
Isso é fundamental para o modelo de marketplace.  
## **4. Solicitação não aponta diretamente para um profissional**  
O profissional aparece através dos orçamentos.  
## **5. Contratação nasce da aceitação de orçamento**  
Solicitação  
    ↓  
Orçamento  
    ↓  
Aceitação  
    ↓  
Contratação  
## **6. Pagamento possui fluxo independente**  
O pagamento possui estados próprios e integração com o Mercado Pago.  
## **7. Cancelamento depende do estado**  
Nem toda solicitação ou contratação pode ser cancelada em qualquer momento.  
# **🚀 Próximo grande marco**  
O próximo objetivo do projeto é alcançar:  
## **MVP FUNCIONAL VALIDADO**  
O ciclo completo deverá funcionar:  
CLIENTE  
   ↓  
SOLICITAÇÃO  
   ↓  
PROFISSIONAIS  
   ↓  
ORÇAMENTOS  
   ↓  
ESCOLHA  
   ↓  
CONTRATAÇÃO  
   ↓  
PAGAMENTO  
   ↓  
EXECUÇÃO  
   ↓  
CONCLUSÃO  
   ↓  
COMISSÃO  
   ↓  
REPASSE  
Somente depois da validação desse ciclo será recomendável concentrar esforços em funcionalidades adicionais.  
# **⭐ Próximas funcionalidades**  
Após a estabilização do MVP:  
1. Sistema de avaliações;  
2. Sistema de reputação;  
3. Notificações;  
4. Melhorias dos dashboards;  
5. Histórico avançado;  
6. Auditoria;  
7. Melhorias de segurança;  
8. Preparação para produção;  
9. Aplicativo mobile.  
# **📌 Princípio de desenvolvimento**  
Durante a evolução do ChamaPro, alterações visuais não devem modificar a lógica de negócio.  
Ao alterar templates, devem ser preservados:  
- URLs;  
- nomes das variáveis;  
- condições;  
- formulários;  
- métodos HTTP;  
- CSRF;  
- ações dos botões;  
- JavaScript;  
- regras de negócio.  
A prioridade deve ser:  
**funcionalidade → estabilidade → segurança → experiência do usuário → novas funcionalidades.**  
# **📄 Documentação**  
Este README deve ser mantido atualizado conforme o projeto evoluir.  
Alterações importantes de arquitetura, modelos, fluxos ou regras de negócio devem ser registradas aqui.  
# **👨‍💻 Status do projeto**  
**ChamaPro Serviços — em desenvolvimento**  
O núcleo do marketplace já está estruturado e diversas funcionalidades estão implementadas.  
O próximo grande objetivo é validar integralmente o fluxo de contratação e pagamento antes da expansão para avaliações, notificações e demais funcionalidades.  
## **ChamaPro Serviços**  
**Precisou? Chame um profissional.**  
   
