export type PurchaseItem = {
  id: number
  produto_id: number
  produto_nome: string
  sku: string
  quantidade: string | number
  quantidade_recebida: string | number
  pendente: string | number
  custo_unitario: string | number
}

export type Purchase = {
  id: number
  numero: string
  fornecedor_id: number
  status: 'RASCUNHO' | 'EMITIDO' | 'PARCIALMENTE_RECEBIDO' | 'RECEBIDO' | 'CANCELADO'
  previsao_entrega: string | null
  observacao: string | null
  created_at: string
  updated_at: string
  itens: PurchaseItem[]
}

export type PurchaseItemPayload = { produto_id: number; quantidade: string; custo_unitario: string }
export type PurchasePayload = { numero?: string; fornecedor_id: number; previsao_entrega?: string | null; observacao?: string | null; itens: PurchaseItemPayload[] }

export type Receipt = {
  id: number
  pedido_id: number
  data_recebimento: string
  status: 'RASCUNHO' | 'CONFIRMADO' | 'CANCELADO'
  usuario_id: number | null
  observacao: string | null
  created_at: string
  updated_at: string
  itens: { id: number; pedido_item_id: number; produto_id: number; quantidade: string | number; custo_efetivo: string | number }[]
}
