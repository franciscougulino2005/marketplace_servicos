from django.core.management.base import BaseCommand
from ajuda.models import CategoriaAjuda, ArtigoAjuda


class Command(BaseCommand):
    help = 'Cria as categorias e os artigos iniciais da Central de Ajuda.'

    def handle(self, *args, **options):

        dados = [

            {
                'nome': 'Começando no ChamaPro',
                'slug': 'comecando-no-chamapro',
                'descricao': (
                    'Orientações para conhecer a plataforma e começar a utilizar '
                    'o ChamaPro Serviços.'
                ),
                'publico': 'todos',
                'icone': '🚀',
                'ordem': 1,
                'artigos': [

                    {
                        'titulo': 'Conhecendo o ChamaPro Serviços',
                        'slug': 'conhecendo-o-chamapro-servicos',
                        'resumo': (
                            'Entenda o que é o ChamaPro Serviços, quem pode utilizar '
                            'a plataforma e como funciona o marketplace.'
                        ),
                        'ordem': 1,
                        'conteudo': """
O ChamaPro Serviços é uma plataforma que aproxima clientes e profissionais
prestadores de serviços.

A plataforma permite que o cliente encontre profissionais, consulte serviços,
envie solicitações e acompanhe suas contratações.

Para o profissional, o ChamaPro oferece recursos para apresentar seus serviços,
receber solicitações, enviar propostas e acompanhar os trabalhos realizados.

## Como funciona

O funcionamento básico da plataforma pode ser resumido em algumas etapas:

1. O usuário realiza seu cadastro.
2. O usuário completa seu perfil.
3. O cliente procura um serviço ou profissional.
4. O cliente envia uma solicitação.
5. O profissional analisa a solicitação.
6. O profissional pode enviar uma proposta.
7. O cliente analisa a proposta.
8. O cliente aceita ou recusa a proposta.
9. A contratação é realizada.
10. O serviço é executado.
11. O cliente e o profissional podem avaliar a experiência.

Os detalhes de cada etapa estão explicados nos demais artigos desta Central de Ajuda.

## Preciso ser profissional para utilizar o ChamaPro?

Não.

A plataforma poderá ser utilizada tanto por clientes que procuram serviços
quanto por profissionais que desejam oferecer seus serviços.

Dependendo do tipo de cadastro e das permissões definidas pela plataforma,
determinadas funcionalidades poderão estar disponíveis para cada perfil.
""",
                    },

                    {
                        'titulo': 'Como acessar a Central de Ajuda',
                        'slug': 'como-acessar-a-central-de-ajuda',
                        'resumo': (
                            'Aprenda a consultar os manuais, procedimentos e respostas '
                            'disponíveis no ChamaPro.'
                        ),
                        'ordem': 2,
                        'conteudo': """
A Central de Ajuda foi criada para concentrar as orientações de utilização
do ChamaPro Serviços.

## Como utilizar

Na Central de Ajuda você pode:

- pesquisar uma dúvida;
- navegar pelas categorias;
- consultar artigos;
- seguir procedimentos passo a passo;
- consultar orientações específicas para clientes;
- consultar orientações específicas para profissionais.

## Pesquisa

Utilize o campo de pesquisa localizado na parte superior da Central de Ajuda.

Digite palavras relacionadas ao assunto que deseja encontrar.

Por exemplo:

- cadastro;
- serviço;
- proposta;
- pagamento;
- contratação;
- cancelamento.

Quanto mais específica for a pesquisa, mais fácil será localizar o artigo desejado.

## Dica

Antes de abrir uma solicitação de suporte, procure primeiro o assunto na Central
de Ajuda. Muitas dúvidas podem ser resolvidas imediatamente através dos manuais.
""",
                    },

                ],
            },

            {
                'nome': 'Para Clientes',
                'slug': 'para-clientes',
                'descricao': (
                    'Tudo o que o cliente precisa saber para encontrar, solicitar '
                    'e contratar serviços.'
                ),
                'publico': 'cliente',
                'icone': '👤',
                'ordem': 2,
                'artigos': [

                    {
                        'titulo': 'Como cadastrar uma conta',
                        'slug': 'como-cadastrar-uma-conta',
                        'resumo': (
                            'Veja como realizar o cadastro para utilizar o ChamaPro '
                            'como cliente.'
                        ),
                        'ordem': 1,
                        'conteudo': """
Para utilizar os recursos destinados aos clientes, é necessário possuir uma
conta cadastrada na plataforma.

## Passo 1 — Acesse o cadastro

Na tela inicial do ChamaPro, selecione a opção para criar uma nova conta.

## Passo 2 — Informe seus dados

Preencha os dados solicitados pelo sistema.

Informe os dados corretamente, principalmente aqueles utilizados para contato.

## Passo 3 — Crie sua senha

Escolha uma senha segura.

Evite utilizar informações fáceis de descobrir, como datas de nascimento,
nome ou telefone.

## Passo 4 — Finalize o cadastro

Depois de preencher os campos obrigatórios, confirme o cadastro.

Após a conclusão, você poderá acessar sua conta utilizando suas credenciais.

## Mantenha seus dados atualizados

É importante manter telefone, e-mail e demais informações atualizados.

Isso facilita a comunicação entre você e os profissionais.
""",
                    },

                    {
                        'titulo': 'Como procurar um serviço',
                        'slug': 'como-procurar-um-servico',
                        'resumo': (
                            'Aprenda a localizar serviços e profissionais disponíveis '
                            'na plataforma.'
                        ),
                        'ordem': 2,
                        'conteudo': """
O ChamaPro permite procurar serviços de acordo com a necessidade do cliente.

## Passo 1

Acesse a área de serviços da plataforma.

## Passo 2

Utilize a pesquisa ou navegue pelas categorias disponíveis.

## Passo 3

Selecione o serviço que deseja conhecer.

Verifique as informações apresentadas pelo profissional, quando disponíveis.

## Passo 4

Caso o serviço atenda à sua necessidade, prossiga para solicitar um atendimento
ou iniciar o processo de contratação.

## Dica

Compare as informações de diferentes profissionais antes de tomar sua decisão.

Observe descrição do serviço, experiência, avaliações e demais informações
disponibilizadas na plataforma.
""",
                    },

                    {
                        'titulo': 'Como solicitar um serviço',
                        'slug': 'como-solicitar-um-servico',
                        'resumo': (
                            'Veja como enviar uma solicitação de serviço para um profissional.'
                        ),
                        'ordem': 3,
                        'conteudo': """
Depois de encontrar o serviço desejado, o cliente poderá enviar uma solicitação.

## Informe corretamente sua necessidade

Descreva o que precisa ser realizado de maneira clara.

Quanto mais informações forem fornecidas, melhor será a compreensão do profissional.

Quando aplicável, informe:

- local do serviço;
- data desejada;
- horário;
- descrição do problema;
- quantidade;
- características específicas;
- outras informações importantes.

## Envie a solicitação

Depois de conferir as informações, envie a solicitação.

O profissional poderá analisar os dados e decidir se deseja atender à solicitação.

## Acompanhe o andamento

Depois do envio, acompanhe o status da solicitação pela plataforma.

Caso o profissional envie uma proposta, ela ficará disponível para análise.
""",
                    },

                    {
                        'titulo': 'Como aceitar uma proposta',
                        'slug': 'como-aceitar-uma-proposta',
                        'resumo': (
                            'Aprenda a analisar e aceitar uma proposta enviada por um profissional.'
                        ),
                        'ordem': 4,
                        'conteudo': """
Quando um profissional responder a uma solicitação com uma proposta,
o cliente deverá analisar as condições apresentadas.

## Antes de aceitar

Confira:

- descrição do serviço;
- valor;
- prazo;
- data;
- condições apresentadas;
- demais informações da proposta.

## Aceitando a proposta

Se estiver de acordo com as condições, utilize a opção de aceitar a proposta.

A partir desse momento, o sistema poderá alterar o status da solicitação
conforme as regras definidas para a contratação.

## Atenção

Leia todas as informações antes de confirmar.

Uma proposta aceita poderá gerar uma contratação e, dependendo das regras
do serviço, poderá haver condições específicas para cancelamento.
""",
                    },

                    {
                        'titulo': 'Como acompanhar uma contratação',
                        'slug': 'como-acompanhar-uma-contratacao',
                        'resumo': (
                            'Saiba como acompanhar o andamento dos serviços contratados.'
                        ),
                        'ordem': 5,
                        'conteudo': """
Depois que uma proposta for aceita, a contratação poderá ser acompanhada
através da área apropriada da plataforma.

Observe o status apresentado pelo sistema.

Dependendo do fluxo definido no ChamaPro, uma contratação poderá passar por
diferentes etapas, como:

- aguardando início;
- agendada;
- em andamento;
- concluída;
- cancelada.

Consulte regularmente suas contratações para acompanhar alterações e
comunicações relacionadas ao serviço.
""",
                    },

                    {
                        'titulo': 'Como avaliar um profissional',
                        'slug': 'como-avaliar-um-profissional',
                        'resumo': (
                            'Veja como registrar sua avaliação após a realização do serviço.'
                        ),
                        'ordem': 6,
                        'conteudo': """
Após a conclusão do serviço, o cliente poderá avaliar a experiência,
quando essa funcionalidade estiver disponível.

A avaliação deve representar sua experiência real com o atendimento.

Considere aspectos como:

- qualidade do serviço;
- cumprimento do combinado;
- pontualidade;
- comunicação;
- profissionalismo.

As avaliações ajudam outros clientes a tomar decisões e também contribuem
para a melhoria dos serviços oferecidos na plataforma.

Utilize sempre uma avaliação justa e respeitosa.
""",
                    },

                ],
            },

            {
                'nome': 'Para Profissionais',
                'slug': 'para-profissionais',
                'descricao': (
                    'Orientações para profissionais que desejam oferecer seus serviços '
                    'através do ChamaPro.'
                ),
                'publico': 'profissional',
                'icone': '🛠️',
                'ordem': 3,
                'artigos': [

                    {
                        'titulo': 'Como cadastrar-se como profissional',
                        'slug': 'como-cadastrar-se-como-profissional',
                        'resumo': (
                            'Aprenda como criar seu perfil profissional na plataforma.'
                        ),
                        'ordem': 1,
                        'conteudo': """
O profissional deve realizar seu cadastro e preencher corretamente as
informações solicitadas pela plataforma.

## Perfil profissional

Um perfil completo facilita que os clientes conheçam o profissional.

Preencha, quando solicitado:

- nome ou identificação profissional;
- descrição;
- área de atuação;
- telefone;
- localização;
- experiência;
- demais informações solicitadas.

## Mantenha o perfil atualizado

Sempre que houver alteração nas suas informações, atualize o cadastro.

Um perfil completo e atualizado transmite maior confiança aos clientes.
""",
                    },

                    {
                        'titulo': 'Como cadastrar um serviço',
                        'slug': 'como-cadastrar-um-servico',
                        'resumo': (
                            'Veja como disponibilizar seus serviços para os clientes.'
                        ),
                        'ordem': 2,
                        'conteudo': """
O cadastro de serviços permite que os clientes encontrem aquilo que você oferece.

## Passo 1

Acesse a área destinada aos seus serviços.

## Passo 2

Selecione a opção para cadastrar um novo serviço.

## Passo 3

Informe os dados solicitados.

Procure criar uma descrição clara e objetiva.

Explique:

- o que o serviço inclui;
- o que não está incluído;
- condições de atendimento;
- prazo estimado;
- região atendida;
- preço, quando aplicável.

## Passo 4

Revise todas as informações.

Depois de confirmar o cadastro, o serviço poderá ser disponibilizado
conforme as regras de publicação da plataforma.
""",
                    },

                    {
                        'titulo': 'Como receber e analisar uma solicitação',
                        'slug': 'como-receber-e-analisar-uma-solicitacao',
                        'resumo': (
                            'Entenda como funciona o recebimento de solicitações enviadas pelos clientes.'
                        ),
                        'ordem': 3,
                        'conteudo': """
Quando um cliente solicita um serviço, a solicitação poderá ficar disponível
para análise do profissional.

Leia atentamente as informações enviadas pelo cliente.

Verifique:

- o que precisa ser realizado;
- local;
- data;
- horário;
- quantidade;
- condições especiais;
- demais informações relevantes.

Se houver informações insuficientes, utilize os canais de comunicação
disponibilizados pela plataforma para esclarecer a necessidade do cliente.

Após analisar a solicitação, o profissional poderá apresentar uma proposta,
quando aplicável.
""",
                    },

                    {
                        'titulo': 'Como enviar uma proposta',
                        'slug': 'como-enviar-uma-proposta',
                        'resumo': (
                            'Aprenda a preparar e enviar uma proposta para um cliente.'
                        ),
                        'ordem': 4,
                        'conteudo': """
A proposta deve apresentar de maneira clara as condições nas quais o
profissional está disposto a realizar o serviço.

Informe os dados solicitados pelo sistema.

Quando aplicável, a proposta poderá conter:

- valor;
- prazo;
- data;
- horário;
- descrição;
- condições;
- observações.

Antes de enviar, revise cuidadosamente os dados.

Depois do envio, o cliente poderá analisar a proposta e decidir se deseja
aceitá-la ou recusá-la.
""",
                    },

                    {
                        'titulo': 'Como acompanhar seus serviços',
                        'slug': 'como-acompanhar-seus-servicos',
                        'resumo': (
                            'Veja como acompanhar solicitações, propostas e contratações.'
                        ),
                        'ordem': 5,
                        'conteudo': """
O profissional deve acompanhar regularmente suas atividades na plataforma.

Entre os itens que podem ser acompanhados estão:

- solicitações recebidas;
- propostas enviadas;
- propostas aceitas;
- serviços agendados;
- serviços em andamento;
- serviços concluídos;
- avaliações recebidas.

Acompanhar os status ajuda a evitar perda de prazos e facilita a organização
dos atendimentos.
""",
                    },

                ],
            },

            {
                'nome': 'Cadastro e Perfil',
                'slug': 'cadastro-e-perfil',
                'descricao': (
                    'Informações sobre cadastro, acesso, dados pessoais e manutenção do perfil.'
                ),
                'publico': 'todos',
                'icone': '👥',
                'ordem': 4,
                'artigos': [

                    {
                        'titulo': 'Como alterar meus dados',
                        'slug': 'como-alterar-meus-dados',
                        'resumo': (
                            'Veja como manter suas informações cadastrais atualizadas.'
                        ),
                        'ordem': 1,
                        'conteudo': """
Mantenha seus dados sempre atualizados para garantir que as comunicações
da plataforma cheguem corretamente.

Acesse seu perfil e procure a opção de edição dos dados.

Depois de alterar as informações, confira os campos antes de salvar.

## Atenção

Alguns dados podem possuir regras específicas para alteração.

Caso determinado campo não possa ser alterado diretamente, siga as orientações
apresentadas pelo sistema ou procure o suporte.
""",
                    },

                    {
                        'titulo': 'Como alterar minha senha',
                        'slug': 'como-alterar-minha-senha',
                        'resumo': (
                            'Aprenda a alterar a senha de acesso à sua conta.'
                        ),
                        'ordem': 2,
                        'conteudo': """
Para proteger sua conta, altere sua senha periodicamente e sempre que suspeitar
que outra pessoa possa ter tido acesso às suas credenciais.

Acesse as configurações da sua conta e procure a opção de alteração de senha.

Informe a senha atual, quando solicitada, e depois informe a nova senha.

Escolha uma senha forte e não compartilhe sua senha com outras pessoas.
""",
                    },

                ],
            },

            {
                'nome': 'Pagamentos',
                'slug': 'pagamentos',
                'descricao': (
                    'Informações relacionadas aos pagamentos e às condições financeiras das contratações.'
                ),
                'publico': 'todos',
                'icone': '💳',
                'ordem': 5,
                'artigos': [

                    {
                        'titulo': 'Como funciona o pagamento',
                        'slug': 'como-funciona-o-pagamento',
                        'resumo': (
                            'Entenda o funcionamento geral dos pagamentos realizados através da plataforma.'
                        ),
                        'ordem': 1,
                        'conteudo': """
O funcionamento do pagamento depende das regras definidas para cada contratação
e das funcionalidades financeiras disponibilizadas pelo ChamaPro.

Antes de confirmar uma contratação, confira:

- valor;
- condições de pagamento;
- eventuais taxas;
- prazo;
- forma de pagamento;
- política de cancelamento.

Todas as informações apresentadas antes da confirmação devem ser lidas
atentamente pelo cliente.

O profissional também deve acompanhar os status financeiros relacionados
aos seus serviços.
""",
                    },

                ],
            },

            {
                'nome': 'Problemas e Cancelamentos',
                'slug': 'problemas-e-cancelamentos',
                'descricao': (
                    'Orientações para situações de cancelamento, problemas ou divergências.'
                ),
                'publico': 'todos',
                'icone': '⚠️',
                'ordem': 6,
                'artigos': [

                    {
                        'titulo': 'Como cancelar uma contratação',
                        'slug': 'como-cancelar-uma-contratacao',
                        'resumo': (
                            'Veja as orientações gerais para solicitar o cancelamento de uma contratação.'
                        ),
                        'ordem': 1,
                        'conteudo': """
Caso seja necessário cancelar uma contratação, procure a opção de cancelamento
disponível na própria contratação.

Antes de confirmar, leia atentamente as condições apresentadas.

Dependendo do estágio da contratação, poderão existir regras diferentes
para o cancelamento.

## Atenção

Não deixe de verificar possíveis consequências financeiras ou operacionais
antes de confirmar o cancelamento.

Se a opção de cancelamento não estiver disponível, procure o suporte da plataforma.
""",
                    },

                    {
                        'titulo': 'O que fazer quando houver um problema com o serviço',
                        'slug': 'o-que-fazer-quando-houver-um-problema-com-o-servico',
                        'resumo': (
                            'Saiba quais procedimentos seguir quando ocorrer um problema durante uma contratação.'
                        ),
                        'ordem': 2,
                        'conteudo': """
Se ocorrer algum problema durante uma contratação, procure primeiro registrar
as informações relevantes através dos recursos disponíveis na plataforma.

Descreva o problema de maneira objetiva.

Informe, quando necessário:

- número da contratação;
- data;
- serviço;
- profissional envolvido;
- descrição do ocorrido;
- evidências ou documentos disponíveis.

Evite resolver situações importantes apenas através de conversas externas
à plataforma quando houver recursos próprios para registro da ocorrência.

Caso não consiga solucionar o problema, procure o suporte.
""",
                    },

                ],
            },

            {
                'nome': 'Segurança',
                'slug': 'seguranca',
                'descricao': (
                    'Boas práticas para manter sua conta e suas informações protegidas.'
                ),
                'publico': 'todos',
                'icone': '🔒',
                'ordem': 7,
                'artigos': [

                    {
                        'titulo': 'Como proteger minha conta',
                        'slug': 'como-proteger-minha-conta',
                        'resumo': (
                            'Conheça boas práticas para manter sua conta segura.'
                        ),
                        'ordem': 1,
                        'conteudo': """
A segurança da conta depende também dos cuidados do próprio usuário.

## Recomendações

Nunca compartilhe sua senha.

Evite utilizar a mesma senha em vários serviços.

Não informe códigos de segurança para terceiros.

Tenha cuidado ao clicar em links recebidos por mensagens ou e-mails.

Sempre confira se está acessando o site ou aplicativo oficial do ChamaPro.

## Suspeita de acesso indevido

Se você suspeitar que outra pessoa acessou sua conta:

1. altere sua senha;
2. verifique seus dados;
3. confira suas solicitações e contratações;
4. verifique atividades que você não reconhece;
5. entre em contato com o suporte, se necessário.

Quanto mais rapidamente o problema for identificado, mais fácil será tomar
as medidas necessárias.
""",
                    },

                ],
            },

            {
                'nome': 'Para Administradores',
                'slug': 'para-administradores',
                'descricao': (
                    'Manuais e procedimentos administrativos para gerenciamento da plataforma.'
                ),
                'publico': 'administrador',
                'icone': '⚙️',
                'ordem': 8,
                'artigos': [

                    {
                        'titulo': 'Gerenciamento da Central de Ajuda',
                        'slug': 'gerenciamento-da-central-de-ajuda',
                        'resumo': (
                            'Aprenda como administrar categorias e artigos da Central de Ajuda.'
                        ),
                        'ordem': 1,
                        'conteudo': """
A Central de Ajuda possui uma área administrativa que permite controlar
categorias e artigos publicados na plataforma.

## Categorias

No gerenciamento de categorias, o administrador pode:

- criar categorias;
- alterar categorias;
- definir o público;
- definir a ordem;
- ativar ou desativar categorias;
- informar descrição;
- definir um ícone.

## Artigos

No gerenciamento de artigos, o administrador pode:

- criar artigos;
- alterar artigos;
- selecionar a categoria;
- definir o título;
- informar um resumo;
- escrever o conteúdo;
- definir a ordem;
- ativar ou desativar artigos.

## Publicação

Um artigo somente deverá ser disponibilizado aos usuários quando seu conteúdo
estiver revisado e adequado ao funcionamento atual da plataforma.

Sempre que uma funcionalidade do ChamaPro for alterada, verifique se os
artigos relacionados precisam ser atualizados.
""",
                    },

                    {
                        'titulo': 'Como criar um novo artigo de ajuda',
                        'slug': 'como-criar-um-novo-artigo-de-ajuda',
                        'resumo': (
                            'Passo a passo para adicionar novos conteúdos à Central de Ajuda.'
                        ),
                        'ordem': 2,
                        'conteudo': """
Para criar um novo artigo, acesse a área administrativa do ChamaPro.

Localize o gerenciamento de Artigos de Ajuda.

Selecione a opção para adicionar um novo artigo.

## Preencha os dados

Informe:

- categoria;
- título;
- slug;
- resumo;
- conteúdo;
- ordem;
- status de publicação.

## Escrevendo o conteúdo

Procure escrever de maneira simples e objetiva.

Sempre que possível:

1. apresente o objetivo;
2. explique o procedimento;
3. organize os passos numericamente;
4. destaque cuidados importantes;
5. informe o resultado esperado.

## Antes de publicar

Revise o texto e confirme se o procedimento descrito corresponde exatamente
ao funcionamento atual do sistema.

Depois da publicação, acesse o artigo como usuário e confira sua apresentação.
""",
                    },

                ],
            },

        ]

        categorias_criadas = 0
        categorias_atualizadas = 0
        artigos_criados = 0
        artigos_atualizados = 0

        for categoria_data in dados:

            artigos = categoria_data.pop('artigos', [])

            categoria, criada = CategoriaAjuda.objects.update_or_create(
                slug=categoria_data['slug'],
                defaults=categoria_data
            )

            if criada:
                categorias_criadas += 1
            else:
                categorias_atualizadas += 1

            for artigo_data in artigos:

                artigo, criado = ArtigoAjuda.objects.update_or_create(
                    slug=artigo_data['slug'],
                    defaults={
                        'categoria': categoria,
                        'titulo': artigo_data['titulo'],
                        'resumo': artigo_data['resumo'],
                        'conteudo': artigo_data['conteudo'].strip(),
                        'ordem': artigo_data['ordem'],
                        'ativo': True,
                    }
                )

                if criado:
                    artigos_criados += 1
                else:
                    artigos_atualizados += 1

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'Central de Ajuda carregada com sucesso!'
            )
        )

        self.stdout.write(
            f'Categorias criadas: {categorias_criadas}'
        )

        self.stdout.write(
            f'Categorias atualizadas: {categorias_atualizadas}'
        )

        self.stdout.write(
            f'Artigos criados: {artigos_criados}'
        )

        self.stdout.write(
            f'Artigos atualizados: {artigos_atualizados}'
        )

        self.stdout.write('')