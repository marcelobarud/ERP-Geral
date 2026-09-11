export type DecimalValue = string | number

export type SaleItemCreate = {
  produto_id: number
  quantidade: string
}

export type SaleCreatePayload = {
  cliente_id: number
  funcionario_id: number
  data_venda: string
  observacao?: string | null
  condicao_pagamento_id?: number | null
  itens: SaleItemCreate[]
}

export type SaleStatus = 'CONCLUIDA' | 'CANCELADA'

export type SaleCustomerSummary = {
  id: number
  nome: string
}

export type SaleEmployeeSummary = {
  id: number
  nome_completo: string
}

export type SaleProductSummary = {
  id: number
  nome: string
}

export type SaleSupplierSummary = {
  id: number
  nome: string
}

export type SaleItem = {
  id: number
  produto: SaleProductSummary
  fornecedor_id: number
  fornecedor: SaleSupplierSummary
  quantidade: DecimalValue
  preco_unitario: DecimalValue
  subtotal: DecimalValue
  created_at?: string
  updated_at?: string
}

export type Sale = {
  id: number
  data_venda: string
  status?: SaleStatus
  cancelada_em?: string | null
  motivo_cancelamento?: string | null
  pedido_id?: number | null
  condicao_pagamento_id?: number | null
  observacao?: string | null
  created_at?: string
  updated_at?: string
  cliente: SaleCustomerSummary
  funcionario: SaleEmployeeSummary
  itens: SaleItem[]
  total: DecimalValue
}
