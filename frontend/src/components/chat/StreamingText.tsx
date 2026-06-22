interface Props {
  text: string
}

export default function StreamingText({ text }: Props) {
  return <span>{text}</span>
}
