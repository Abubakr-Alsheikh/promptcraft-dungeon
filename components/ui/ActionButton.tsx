import { Button, ButtonProps } from "@chakra-ui/react";
import { ReactElement } from "react";

interface ActionButtonProps extends ButtonProps {
  label: string;
  icon?: ReactElement;
  onClickAction?: () => void;
}

export function ActionButton({
  label,
  icon,
  onClickAction,
  isLoading,
  isDisabled,
  ...rest
}: ActionButtonProps) {
  return (
    <Button
      leftIcon={icon}
      onClick={onClickAction}
      isLoading={isLoading}
      isDisabled={isDisabled || isLoading}
      colorScheme="gray"
      variant="outline"
      borderColor="brand.secondary"
      color="brand.textLight"
      _hover={{ bg: "brand.secondary", color: "white" }}
      {...rest}
    >
      {label}
    </Button>
  );
}
