import { LoadingState } from './LoadingState'

type CadastrosListLoadingProps = {
  label: string
}

export function CadastrosListLoading({ label }: CadastrosListLoadingProps) {
  return (
    <div className="cadastros-loading-layout">
      <LoadingState label={label} />
      <div className="cadastros-table-skeleton" aria-hidden="true">
        {Array.from({ length: 6 }, (_, index) => <span key={index} />)}
      </div>
    </div>
  )
}
