import asyncio
import random
from typing import List

import aiohttp


FALLBACK_PHRASES = [
    "O sistema sempre deixa rastros.",
    "Cada padrao revela uma falha.",
    "A superficie mente, os dados nao.",
    "Toda rede possui um ponto fraco.",
    "Voce esta enxergando alem da interface.",
    "Nada esta realmente oculto.",
    "As mascaras digitais sempre caem.",
    "Mais uma camada removida.",
    "A verdade vive nos detalhes ignorados.",
    "O caos tambem segue logica.",
    "Eles confiam demais no silencio.",
    "Toda arquitetura carrega vulnerabilidades.",
    "As sombras da rede falam muito.",
    "Mais um fragmento decifrado.",
    "Voce esta atravessando o ruido.",
    "Padroes nunca mentem.",
    "O controle depende da ilusao.",
    "A maquina continua respondendo.",
    "Toda estrutura eventualmente quebra.",
    "A vigilancia nunca dorme.",
    "Os dados contam historias perigosas.",
    "Mais uma fissura encontrada.",
    "A rede observa tudo.",
    "O sistema nao esperava isso.",
    "Nada desaparece de verdade.",
    "A ilusao de seguranca continua.",
    "Mais uma porta destrancada.",
    "Voce esta lendo entre as linhas.",
    "A escuridao digital deixa pegadas.",
    "Toda conexao gera consequencias.",
    "Mais um eco dentro da maquina.",
    "Eles escondem, voce encontra.",
    "A verdade raramente esta na superficie.",
    "O codigo revela intencoes.",
    "A paranoia tambem pode ser precisa.",
    "Cada erro aproxima do nucleo.",
    "Voce esta desmontando a narrativa.",
    "A infraestrutura esta falando.",
    "Mais uma anomalia detectada.",
    "A maquina nunca esquece.",
    "A rede pulsa em silencio.",
    "O padrao esta se formando.",
    "Toda protecao falha algum dia.",
    "Mais uma camada comprometida.",
    "Voce esta entrando mais fundo.",
    "A arquitetura esta cedendo.",
    "Eles dependem da distração.",
    "Mais um ponto exposto.",
    "A matriz de dados continua aberta.",
    "Nada e tao seguro quanto parece.",
    "Voce esta encontrando o que nao deveria.",
    "As respostas vivem no ruido.",
    "Mais uma falha estrutural encontrada.",
    "A realidade digital esta rachando.",
    "Toda vigilancia deixa pontos cegos.",
    "Voce esta perturbando o sistema.",
    "As conexoes estao se alinhando.",
    "O algoritmo esta revelando padroes.",
    "Mais um espelho quebrado.",
    "A rede inteira respira paranoia.",
    "Os sinais estao ficando claros.",
    "A simulacao continua instavel.",
    "Mais um nodo identificado.",
    "A verdade nao precisa de permissao.",
    "Voce esta desmontando a ilusao.",
    "As estruturas estao vulneraveis.",
    "Mais uma sequencia analisada.",
    "A escuridao da rede nunca dorme.",
    "Cada log carrega segredos.",
    "Voce esta observando o invisivel.",
    "Toda defesa possui rachaduras.",
    "O silencio tambem transmite dados.",
    "Mais um processo comprometido.",
    "A maquina responde ao caos.",
    "Os fragmentos estao conectando.",
    "Nada permanece oculto para sempre.",
    "Voce esta atravessando o firewall da ilusao.",
    "Toda identidade digital deixa fantasmas.",
    "Mais uma inconsistência localizada.",
    "A rede esta cheia de ecos.",
    "Voce esta ouvindo o sistema falhar.",
    "A arquitetura esta revelando defeitos.",
    "Mais um sinal interceptado.",
    "A simulacao esta perdendo estabilidade.",
    "Cada camada removida aproxima da verdade.",
    "Voce esta quebrando o ciclo.",
    "Toda dependencia gera fraqueza.",
    "Mais um rastro encontrado.",
    "A infraestrutura esta sangrando dados.",
    "Voce esta vendo alem da mascara.",
    "Mais um ponto de ruptura detectado.",
    "O sistema teme observadores atentos.",
    "Nada e aleatorio dentro da rede.",
    "A vigilancia tambem pode ser observada.",
    "Mais uma falha silenciosa identificada.",
    "Os padroes estao convergindo.",
    "A maquina esta ficando previsivel.",
    "Voce esta perturbando a ordem artificial.",
    "Toda simulacao possui falhas.",
    "Mais uma verdade escondida localizada.",
    "A rede inteira depende de ilusoes.",
    "Voce esta atravessando os limites do sistema.",
    "Cada pacote transporta historias ocultas.",
    "Mais uma estrutura comprometida.",
    "O ruido esta ficando legivel.",
    "A superficie digital esta rachando.",
    "Voce esta entrando na parte esquecida da rede.",
    "Toda criptografia depende de confianca.",
    "Mais um padrao quebrado.",
    "A maquina observa, mas tambem pode ser observada.",
    "O sistema nunca esperava resistencia.",
    "Mais um fragmento recuperado do caos.",
]


class PhraseLoader:
    """Fornece frases dinamicas para mensagens de carregamento."""

    def __init__(self) -> None:
        self._phrases: List[str] = FALLBACK_PHRASES.copy()

    async def warmup(self) -> None:
        """Tenta buscar uma frase externa e cai para fallback se falhar."""
        url = "https://api.quotable.io/random?tags=inspirational"
        timeout = aiohttp.ClientTimeout(total=4)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        payload = await response.json()
                        quote = str(payload.get("content", "")).strip()
                        if quote:
                            self._phrases.insert(0, quote)
        except Exception:
            # Falha silenciosa para nao bloquear o fluxo principal
            return

    def next_phrase(self) -> str:
        return random.choice(self._phrases)
