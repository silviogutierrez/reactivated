import React from "react";

export default <TContext extends {}>() => {
    type TMutableContext = TContext & {
        setValue: React.Dispatch<React.SetStateAction<TContext>>;
    };

    const Context = React.createContext<TMutableContext>(null!);

    const Provider = (props: {value: TContext; children: React.ReactNode}) => {
        const [value, setValue] = React.useState(props.value);

        return (
            <Context.Provider value={{...value, setValue}}>
                {props.children}
            </Context.Provider>
        );
    };

    return {Context, Provider};
};
