export type PaymentCondition = {
  id: number
  codigo: string
  nome: string
  descricao: string | null
  ativo: boolean
}

export type CommercialItem = {
  id: number
  produto_id: number
  produto_nome: string
  sku: string
  fornecedor_id: number
  fornecedor_nome: string
  quantidade: string | number
  preco_unitario: string | number
  desconto: string | number
  acrescimo: string | number
  total: string | number
}

export type CommercialItemPayload = {
  produto_id: number
  quantidade: string
  preco_unitario?: string
  desconto?: string
  acrescimo?: string
}

export type QuoteStatus = 'RASCUNHO' | 'ENVIADO' | 'APROVADO' | 'RECUSADO' | 'EXPIRADO' | 'CANCELADO'
export type OrderStatus = 'RASCUNHO' | 'CONFIRMADO' | 'CONCLUIDO' | 'CANCELADO'

export type CommercialDocumentBase = {
  id: number
  numero: string
  cliente_id: number
  funcionario_id: number | null
  condicao_pagamento_id: number | null
  desconto: string | number
  acrescimo: string | number
  frete: string | number
  status: QuoteStatus | OrderStatus
  observacao: string | null
  itens: CommercialItem[]
  subtotal: string | number
  total: string | number
  created_at: string
  updated_at: string
}

export type Quote = CommercialDocumentBase & {
  validade: string | null
  pedido_id: number | null
}

export type Order = CommercialDocumentBase & {
  orcamento_id: number | null
  venda_id: number | null
}

export type CommercialDocumentPayload = {
  numero?: string
  cliente_id: number
  funcionario_id?: number | null
  condicao_pagamento_id?: number | null
  validade?: string | null
  desconto?: string
  acrescimo?: string
  frete?: string
  observacao?: string | null
  itens: CommercialItemPayload[]
}

export type SaleReturnItem = {
  id: number
  venda_item_id: number
  produto_id: number
  produto_nome: string
  quantidade: string | number
  preco_unitario: string | number
}

export type SaleReturn = {
  id: number
  venda_id: number
  status: 'RASCUNHO' | 'APROVADA' | 'CANCELADA'
  motivo: string
  usuario_id: number | null
  created_at: string
  updated_at: string
  itens: SaleReturnItem[]
}
