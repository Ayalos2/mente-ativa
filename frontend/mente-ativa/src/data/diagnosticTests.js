export const createId = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, '-')

export const shuffleArray = (items) => {
  const copy = [...items]

  for (let index = copy.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1))
    const temporary = copy[index]
    copy[index] = copy[randomIndex]
    copy[randomIndex] = temporary
  }

  return copy
}

export const memoryStimuli = [
  { id: 'casa', label: 'Casa', icon: '🏠' },
  { id: 'livro', label: 'Livro', icon: '📖' },
  { id: 'copo', label: 'Copo', icon: '🥛' },
  { id: 'janela', label: 'Janela', icon: '🪟' },
  { id: 'chave', label: 'Chave', icon: '🗝️' },
  { id: 'arvore', label: 'Árvore', icon: '🌳' },
  { id: 'cachorro', label: 'Cachorro', icon: '🐶' },
  { id: 'pao', label: 'Pão', icon: '🍞' },
  { id: 'flor', label: 'Flor', icon: '🌷' },
  { id: 'mesa', label: 'Mesa', icon: '🪑' },
  { id: 'luz', label: 'Luz', icon: '💡' },
  { id: 'bola', label: 'Bola', icon: '⚽' },
]

export const semanticCategories = {
  animais: {
    id: 'animais',
    label: 'Animais',
    description: 'Selecione o maior número possível de animais no tempo disponível.',
    correct: [
      { id: 'cachorro', label: 'Cachorro', icon: '🐶' },
      { id: 'gato', label: 'Gato', icon: '🐱' },
      { id: 'elefante', label: 'Elefante', icon: '🐘' },
      { id: 'leao', label: 'Leão', icon: '🦁' },
      { id: 'tartaruga', label: 'Tartaruga', icon: '🐢' },
      { id: 'peixe', label: 'Peixe', icon: '🐟' },
      { id: 'coelho', label: 'Coelho', icon: '🐰' },
      { id: 'passaro', label: 'Pássaro', icon: '🐦' },
    ],
    distractors: [
      { id: 'copo', label: 'Copo', icon: '🥛' },
      { id: 'mesa', label: 'Mesa', icon: '🪑' },
      { id: 'panela', label: 'Panela', icon: '🍳' },
      { id: 'chave', label: 'Chave', icon: '🗝️' },
      { id: 'camisa', label: 'Camisa', icon: '👕' },
      { id: 'caderno', label: 'Caderno', icon: '📒' },
    ],
  },
  cozinha: {
    id: 'cozinha',
    label: 'Objetos de Cozinha',
    description: 'Selecione os itens relacionados à cozinha por 60 segundos.',
    correct: [
      { id: 'panela', label: 'Panela', icon: '🍳' },
      { id: 'garfo', label: 'Garfo', icon: '🍴' },
      { id: 'faca', label: 'Faca', icon: '🔪' },
      { id: 'prato', label: 'Prato', icon: '🍽️' },
      { id: 'copo', label: 'Copo', icon: '🥛' },
      { id: 'colher', label: 'Colher', icon: '🥄' },
      { id: 'frigideira', label: 'Frigideira', icon: '🍳' },
      { id: 'liquidificador', label: 'Liquidificador', icon: '🥤' },
    ],
    distractors: [
      { id: 'sapato', label: 'Sapato', icon: '👟' },
      { id: 'arvore', label: 'Árvore', icon: '🌳' },
      { id: 'bola', label: 'Bola', icon: '⚽' },
      { id: 'janela', label: 'Janela', icon: '🪟' },
      { id: 'livro', label: 'Livro', icon: '📖' },
      { id: 'camisa', label: 'Camisa', icon: '👕' },
    ],
  },
}

export const trailSequence = [
  { id: '1', label: '1', kind: 'number' },
  { id: 'A', label: 'A', kind: 'letter' },
  { id: '2', label: '2', kind: 'number' },
  { id: 'B', label: 'B', kind: 'letter' },
  { id: '3', label: '3', kind: 'number' },
  { id: 'C', label: 'C', kind: 'letter' },
  { id: '4', label: '4', kind: 'number' },
  { id: 'D', label: 'D', kind: 'letter' },
  { id: '5', label: '5', kind: 'number' },
  { id: 'E', label: 'E', kind: 'letter' },
  { id: '6', label: '6', kind: 'number' },
  { id: 'F', label: 'F', kind: 'letter' },
]

export const diagnosticRoutes = {
  nback: '/testes/memoria-curto-prazo',
  fluency: '/testes/fluencia-semantica',
  trail: '/testes/atencao-alternada',
}
