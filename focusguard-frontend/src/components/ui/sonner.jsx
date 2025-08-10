import { Toaster as Sonner } from "sonner";

const Toaster = ({
  ...props
}) => {
  return (
    <Sonner
      theme="light"
      className="toaster group"
      position="top-right"
      richColors={true}
      closeButton={true}
      {...props} />
  );
}

export { Toaster }
