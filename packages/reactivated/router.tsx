// Useful:
// https://dev.to/thomascullen/build-a-react-router-clone-from-scratch-38dp

/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/ban-types */

import {current} from "immer";
import React from "react";
import {NodeArray} from "typescript";

export type ExtractRouteParams<T> = string extends T
    ? Record<string, string | number>
    : T extends `${infer _Start}<string:${infer Param}>/${infer Rest}`
    ? ExtractRouteParams<_Start> & {[k in Param]: string} & ExtractRouteParams<Rest>
    : T extends `${infer _Start}<number:${infer Param}>/${infer Rest}`
    ? ExtractRouteParams<_Start> & {[k in Param]: number} & ExtractRouteParams<Rest>
    : T extends `${infer _Start}<string:${infer Param}>`
    ? {[k in Param]: string}
    : T extends `${infer _Start}<number:${infer Param}>`
    ? {[k in Param]: number}
    : Record<never, never>;

// import {AnimatePresence, motion} from "framer-motion";

type Resolvable = Promise<Record<string, any>> | Record<string, any>;

const REGEX = /<(string|number):([\w]*)>/g;

const processRoutePath = <TPath extends string, TTabs extends string[]>(
    path: TPath,
    tabs: [...TTabs],
) => {
    type Tokens = Record<
        Extract<keyof ExtractRouteParams<TPath>, string>,
        "string" | "number"
    >;
    const tokens = [...path.matchAll(REGEX)].map((token) => {
        return [token[2] as keyof Tokens, token[1] as "string" | "number"] as const;
    });
    const pattern = "/".concat(path.replace(/<(string|number)/g, "").replace(/>/g, ""));

    let regexPattern = pattern.replace(/:(\w+)/g, () => {
        return "([^\\/]+)";
    });

    if (tabs.length > 1) {
        const validTabs = tabs.slice(1).join("|");
        regexPattern = regexPattern.concat(`(?:$|(?<tab>${validTabs})\/$)`);
    } else {
        regexPattern = regexPattern.concat("$");
    }

    const regex = new RegExp(`^(${regexPattern})`, "i");

    return {
        tokens,
        pattern,
        regex,
    };
};

export const interpolatePath = (pattern: string, params: Record<string, any>) => {
    return pattern.replace(
        /:(\w+)/g,
        (placeholderWithDelimiters, placeholderWithoutDelimiters: string) => {
            return params[placeholderWithoutDelimiters];
        },
    );
};

type WithTab<TTabs extends string[], TTabsSoFar extends string[], TProps> = {
    <TTab extends TTabs[number], TGuardedProps = TProps>(
        definition: {
            name: TTab;
            guard?: (props: TProps) => TGuardedProps | false;
        },
        component: React.ComponentType<TGuardedProps>,
    ): {
        withTab: WithTab<TTabs, [...TTabsSoFar, TTab], TProps>;
        withActions: WithActions<TProps>;
        options: () => {title: string};
        hooks: (props: TProps) => TProps;
        actions: () => [];
        tabs: {
            [K in [...TTabsSoFar, TTab][number]]: {
                component: typeof component;
                options: {
                    name: string;
                };
            };
        };
    };
};

type WithComponent<TProps> = {
    (component: React.ComponentType<TProps>): {
        withActions: WithActions<TProps>;
        options: () => {title: string};
        hooks: (props: TProps) => TProps;
        actions: () => [];
        tabs: {
            index: {
                component: typeof component;
                options: {
                    name: string;
                };
            };
        };
    };
};

type Action = {
    name: string;
    onClick: () => void;
};

export type ActionsDefinition =
    | ([] & ReadonlyArray<Action>)
    | readonly [Action]
    | readonly [Action, Action]
    | readonly [Action, Action, Action]
    | readonly [Action, Action, Action, Action]
    | readonly [Action, Action, Action, Action, Action]
    | readonly [Action, Action, Action, Action, Action, Action];

export type OptionsDefinition = {title: string};

type WithOptions<TProps> = {
    (options: (props: TProps) => OptionsDefinition): {
        hooks: (props: TProps) => any;
        tabs: TabMap<string[]>;
        actions: (props: TProps) => ActionsDefinition;
        options: typeof options;
    };
};

type WithActions<TProps> = {
    (actions: (props: TProps) => ActionsDefinition): {
        actions: typeof actions;
        tabs: TabMap<string[]>;
        hooks: (props: TProps) => any;
        // withOptions: WithOptions<TProps>;
        options: () => {title: string};
        withOptions: WithOptions<TProps>;
    };
};

/*
        const withTab = <
            TTabName extends string,
            TGuardedProps = TProps &
                TComponentProps<TTabName> &
                JoySpecificUtilities<ExtractRouteParams<TPath>, TTabs, TResolve>
        >(
            options: {
                name: TTabName;
                guard?: (
                    props: TProps &
                        TComponentProps<TTabName> &
                        JoySpecificUtilities<
                            ExtractRouteParams<TPath>,
                            TTabs,
                            TResolve
                        >,
                ) => TGuardedProps | false;
            } & JoySpecificTab<TGuardedProps>,
            component: React.ComponentType<TGuardedProps>,
        ) => {
            */

type MyThing<TTabs extends string[]> = {
    withTab: (tab: TTabs[number]) => MyThing<TTabs>;
};

function myThing<TTabs extends string[] = ["index"]>(options: {
    tabs?: [...TTabs];
}): MyThing<TTabs> {
    return null as any;
    /*

    const addTab = (tab: TTabs[number]) => {
    }

    return {tabs: options.tabs, addTab};
    */
}

// const result = myThing({})

// result.withTab("a")

import {Result} from "./rpc";

type RemoveNulls<T> = {[K in keyof T]: NonNullable<T[K]>};

type ExtractResult<T> = T extends Result<any, any>
    ? RemoveNulls<DiscriminateUnion<T, "type", "success">>
    : RemoveNulls<T>;

type TryIt<T> = T extends Promise<infer U> ? ExtractResult<U> : ExtractResult<T>;

export type Route<
    TName extends string,
    TParent extends string | null,
    TPath extends string,
    TResolve,
    TResolvedSoFar,
    TGlobalHooks,
    THooks, // TODO: Not sure THooks is actually needed. Seems to be done at the local function level.
    TTabs extends string[] = ["index"],
> = RouteDefinition<
    TName,
    TParent,
    TPath,
    TResolve,
    TResolvedSoFar,
    TGlobalHooks,
    THooks,
    TTabs
> & {
    resolve?: (props: {params: ExtractRouteParams<TPath>}) => TResolve;
    tabs?: [...TTabs];
    subroute: <
        TInnerName extends string,
        TInnerPath extends string,
        TInnerResolve,
        TInnerTabs extends string[] = ["index"],
    >(innerOptions: {
        name: TInnerName;
        path: TInnerPath;
        tabs?: [...TInnerTabs];
        resolve?: (props: {
            params: ExtractRouteParams<`${TPath}${TInnerPath}`>;
            resolved: TResolvedSoFar;
        }) => TInnerResolve;
    }) => Route<
        TInnerName,
        TName,
        `${TPath}${TInnerPath}`,
        TInnerResolve,
        TryIt<TInnerResolve> & TResolvedSoFar,
        TGlobalHooks,
        THooks,
        TInnerTabs
    >;
    withTab: WithTab<TTabs, [], {resolved: TryIt<TResolve> & TResolvedSoFar}>;
    withHooks: <TLocalHooks>(
        hooks: (props: {resolved: TryIt<TResolve> & TResolvedSoFar}) => TLocalHooks,
    ) => {
        withTab: WithTab<
            TTabs,
            [],
            TLocalHooks & {resolved: TryIt<TResolve> & TResolvedSoFar}
        >;
        withComponent: WithComponent<
            TLocalHooks & {
                currentTab: TTabs[number];
                resolved: TryIt<TResolve> & TResolvedSoFar;
            }
        >;
    };
    withComponent: WithComponent<{
        currentTab: TTabs[number];
        resolved: TryIt<TResolve> & TResolvedSoFar;
    }>;
};

type RouteDefinition<
    TName extends string,
    TParent extends string | null,
    TPath extends string,
    TResolve,
    TResolvedSoFar,
    TGlobalHooks,
    THooks,
    TTabs extends string[],
> = {
    name: TName;
    definition: {
        parent: TParent;
        path: TPath;
        tabs: [...TTabs];
        resolve: {
            hack(props: {
                // Not sure why string is needed here instead of TPath.
                params: ExtractRouteParams<TPath>;
                resolved: TResolvedSoFar;
            }): TResolve;
        }["hack"];
        hooks: () => TGlobalHooks;

        _testing: {
            params: ExtractRouteParams<TPath>;
            resolved: TryIt<TResolve> & TResolvedSoFar;
            tabs: TTabs;
            tab: TTabs[number];
            hooks: TGlobalHooks;
        };
    };
    processed: {
        pattern: string;
        tokens: Array<readonly [string, "string" | "number"]>;
        regex: RegExp;
    };
};

// TODO: Import from reactivated/types
type DiscriminateUnion<T, K extends keyof T, V extends T[K]> = T extends Record<K, V>
    ? T
    : never;

// TODO: this is probably wrong.
type Tab<TProps, TGuard = TProps> = {
    options: {
        name: string;
        guard?: (props: TProps) => TGuard;
    };
    component: React.ComponentType<TProps>;
};

type TabMap<TTabNames extends string[]> = {
    [K in TTabNames[number]]: Tab<any>;
};

interface StaticRouteImplementation<TTabs extends string[]> {
    tabs: TabMap<TTabs>;
    actions: (props: any) => ActionsDefinition;
    options: (props: any) => OptionsDefinition;
    hooks: (props: any) => any;
    // actions: (props: any) => ActionsDefinition;
    // options: SceneOptions<any>;
}

type RouteImplementation<TTabs extends string[]> = StaticRouteImplementation<TTabs>;

export const matchRoutes = <
    TRoutes extends Array<
        RouteDefinition<string, string | null, any, any, any, any, any, any>
    >,
>(
    routes: [...TRoutes],
    path: string,
) => {
    for (const route of routes) {
        const match = path.match(route.processed.regex);

        if (match != null) {
            const tab = match.groups?.tab ?? route.definition.tabs[0];
            const uncastedParams = match.slice(2);

            const params = Object.fromEntries<string | number>(
                route.processed.tokens.map(([tokenName, tokenType], index) => {
                    const uncastedParam = uncastedParams[index];
                    if (tokenType === "number") {
                        return [tokenName, parseInt(uncastedParam)] as const;
                    }
                    return [tokenName, uncastedParam] as const;
                }),
            );

            return {route, params, tab};
        }
    }
    return null;
};

const nominal: unique symbol = Symbol("locator");

// TODO: how do we get this to use RouteNames and TRoutes, inside createRouter.
interface Locator {
    symbol: typeof nominal;
    name: string;
    tab: string;
    params: Record<string, string | number>;
    scenePath: string;
    routeDefinition: RouteDefinition<
        string,
        string | null,
        string,
        any,
        any,
        any,
        any,
        string[]
    >;
    resolved?: any;
    url: string;
    method: "push" | "replace";
}

export const createRouter = <
    TRoutes extends Array<
        RouteDefinition<string, string | null, any, any, any, any, any, any>
    >,
>(
    routes: [...TRoutes],
) => {
    // Maybe strip route function / concat from here?

    type RouteNames = TRoutes[Extract<keyof TRoutes, number>]["name"];

    /*
    interface Locator {
        symbol: typeof nominal;
        name: RouteNames;
        tab: TRoutes[number]["definition"]["tabs"][number];
        params: Record<string, string | number>;
        scenePath: string;
        routeDefinition: RouteDefinition<string, string | null, string, any, any, any, string[]>;
        resolved?: any;
        url: string;
        method: "push" | "replace";
    }
    */

    const locator = <
        TName extends RouteNames,
        TParams extends ExtractRouteParams<
            DiscriminateUnion<TRoutes[number], "name", TName>["definition"]["path"]
        >,
        TTab extends DiscriminateUnion<
            TRoutes[number],
            "name",
            TName
        >["definition"]["tabs"][number],
        TResolve extends ReturnType<
            DiscriminateUnion<TRoutes[number], "name", TName>["definition"]["resolve"]
        >,
    >(target: {
        route: `${TName}.${TTab}`;
        params: TParams;
        replace?: true;
        method?: "push" | "replace";
        resolved?: TryIt<TResolve>;
    }): Locator => {
        const [routeName, tabName] = target.route.split(".");
        const routeDefinition = Object.values(routes).find(
            (route) => route.name == routeName,
        );
        if (routeDefinition == null) {
            throw new Error(`Invalid route ${routeName}`);
        }
        const scenePath = interpolatePath(
            routeDefinition.processed.pattern,
            target.params,
        );
        const url =
            tabName == routeDefinition.definition.tabs[0]
                ? scenePath
                : `${scenePath}${tabName}/`;
        return {
            symbol: nominal,
            scenePath,
            url,
            routeDefinition,
            name: routeName as TName,
            tab: tabName as TTab,
            params: target.params,
            resolved: target.resolved,
            method: target.method ?? "push",
        };
    };
    const getLocatorFromURL = (path: string, method: "push" | "replace" = "push") => {
        const match = matchRoutes(routes, path);

        if (match == null) {
            return null;
        }

        const {route, params} = match;

        const scenePath = interpolatePath(route.processed.pattern, params);
        const possibleTab = path.replace(scenePath, "").slice(0, -1);

        const tab: string = possibleTab === "" ? route.definition.tabs[0] : possibleTab;
        return locator({
            route: `${route.name}.${tab}`,
            params: params as any,
            method,
        });
    };

    type Dependencies = Readonly<Record<string, unknown>>;

    const dependencies: Dependencies = {};

    const setResolved = (resolved: Dependencies) => {
        Object.assign(dependencies, resolved);
        const navigationEvent = new Event("resolved");
        window.dispatchEvent(navigationEvent);
    };

    type ResolveContext = {
        dependecies: Dependencies;
    };

    const ResolveContext = React.createContext<ResolveContext>(undefined!);

    const ResolveProvider = (props: {children: React.ReactNode}) => {
        const [mirror, setMirror] = React.useState(dependencies);

        React.useEffect(() => {
            const handleResolved = () => setMirror({...dependencies});
            const listener = window.addEventListener("resolved", handleResolved);

            return () => {
                window.removeEventListener("resolved", handleResolved);
            };
        }, []);

        return (
            <ResolveContext.Provider value={{dependecies: mirror}}>
                {props.children}
            </ResolveContext.Provider>
        );
    };

    const reverse = <
        TName extends RouteNames,
        TParams extends ExtractRouteParams<
            DiscriminateUnion<TRoutes[number], "name", TName>["definition"]["path"]
        >,
        TTab extends DiscriminateUnion<
            TRoutes[number],
            "name",
            TName
        >["definition"]["tabs"][number],
    >(
        routeNameAndTab: `${TName}.${TTab}`,
        params: TParams,
    ) => {
        const [routeName, tabName] = routeNameAndTab.split(".");
        const match = Object.values(routes).find((route) => route.name == routeName)!;
        const url = interpolatePath(match.processed.pattern, params);
        if (tabName === match.definition.tabs[0]) {
            return {url, match};
        }
        return {url: `${url}${tabName}/`, match};
    };

    const push = async <
        TName extends RouteNames,
        TParams extends ExtractRouteParams<
            DiscriminateUnion<TRoutes[number], "name", TName>["definition"]["path"]
        >,
        TTab extends DiscriminateUnion<
            TRoutes[number],
            "name",
            TName
        >["definition"]["tabs"][number],
        TResolve extends DiscriminateUnion<
            TRoutes[number],
            "name",
            TName
        >["definition"]["_testing"]["resolved"],
    >(
        routeNameAndTab: `${TName}.${TTab}`,
        params: TParams,
        resolved?: TryIt<TResolve>,
    ) => {
        return transition(
            locator({route: routeNameAndTab, params, resolved, method: "push"}),
        );
    };

    const transition = async (target: Locator) => {
        const source = getLocatorFromURL(location.pathname);
        const match = target.routeDefinition;

        if (target.resolved != null) {
            setResolved({
                [target.scenePath]: target.resolved,
            });
        } else if (source == null || source.scenePath != target.scenePath) {
            const resolved = await match.definition.resolve({
                params: target.params,
                resolved: {},
            });
            setResolved({
                [target.scenePath]: resolved,
            });
        }

        if (target.method == "replace") {
            history.replaceState(null, "", target.url);
        } else {
            history.pushState(null, "", target.url);
        }
        const navigationEvent = new PopStateEvent("navigate");
        window.dispatchEvent(navigationEvent);
    };

    const Link = <
        TName extends RouteNames,
        TParams extends ExtractRouteParams<
            DiscriminateUnion<TRoutes[number], "name", TName>["definition"]["path"]
        >,
        TTab extends DiscriminateUnion<
            TRoutes[number],
            "name",
            TName
        >["definition"]["tabs"][number],
        TResolve extends ReturnType<
            DiscriminateUnion<TRoutes[number], "name", TName>["definition"]["resolve"]
        >,
    >(
        props:
            | {
                  locator: Locator;
                  url?: never;
                  method?: never;
                  route?: never;
                  params?: never;
                  resolved?: never;
                  children: React.ReactNode;
                  className?: string;
                  style?: React.CSSProperties;
                  onClick?: () => void;
              }
            | {
                  locator?: never;
                  url?: never;
                  method?: never;
                  route: `${TName}.${TTab}`;
                  params: TParams;
                  resolved?: TryIt<TResolve>;
                  children: React.ReactNode;
                  className?: string;
                  style?: React.CSSProperties;
                  onClick?: () => void;
              }
            | {
                  locator?: never;
                  url: string;
                  method?: "push" | "replace";
                  route?: never;
                  params?: never;
                  resolved?: never;
                  children: React.ReactNode;
                  className?: string;
                  style?: React.CSSProperties;
                  onClick?: () => void;
              },
    ) => {
        const target =
            props.locator != null
                ? props.locator
                : props.url != null
                ? getLocatorFromURL(props.url, props.method)
                : locator(props);

        if (target == null) {
            console.warn(`Invalid <Link> with URL "${props.url ?? ""}"`);
            return (
                <a className={props.className} href={props.url}>
                    {props.children}
                </a>
            );
        }

        const onClick: React.MouseEventHandler = (event) => {
            event.preventDefault();
            props.onClick?.();

            void transition(target);
        };
        return (
            <a
                className={props.className}
                href={target.url}
                style={props.style}
                onClick={onClick}
            >
                {props.children}
            </a>
        );
    };

    const mount = (implementations: {
        [K in RouteNames]: RouteImplementation<
            DiscriminateUnion<TRoutes[number], "name", K>["definition"]["tabs"]
        >;
    }) => {
        const Loader = (props: {
            match: any;
            hooks: any;
            locator: Locator;
            component: React.ComponentType;
        }) => {
            const {dependecies} = React.useContext(ResolveContext);
            const {locator, component: Component, match} = props;
            const {route, params} = match;
            const currentResolved = dependencies[locator.scenePath];

            // const [isLoaded, setIsLoaded] = React.useState(currentResolved != null);
            const isLoaded = currentResolved != null;

            React.useEffect(() => {
                if (isLoaded == false) {
                    (async () => {
                        setResolved({
                            [locator.scenePath]: await route.definition.resolve({
                                params,
                            }),
                        });
                        // setIsLoaded(true);
                    })();
                }
            }, []);

            if (isLoaded == false) {
                return <div>Loading...</div>;
            }

            const componentProps = {
                ...props.hooks({resolved: currentResolved}),
                resolved: currentResolved,
            };

            return <Component {...(componentProps as any)} />;
        };

        const Loaded = ({
            currentResolved,
            currentLocator,
            implementation,
            parent,
            match,
            children,
        }: {
            match: any;
            currentLocator: Locator;
            currentResolved: any;
            implementation: any;
            parent: any;
            children: RenderProps;
        }) => {
            const {route} = match;
            const hooks = implementation.hooks({resolved: currentResolved});
            const options = implementation.options({
                ...hooks,
                resolved: currentResolved,
            });
            const actions = implementation.actions({
                ...hooks,
                resolved: currentResolved,
            });
            const tabs = Object.values<Tab<unknown>>(implementation.tabs).map((tab) => {
                const tabLocator = locator({
                    route: `${route.name}.${tab.options.name}`,
                    params: match.params,
                });

                return {
                    locator: tabLocator,
                    url: tabLocator.url,
                    name: tab.options.name,
                    isActive: tabLocator.url == currentLocator.url,
                };
            });
            const componentProps = {
                ...hooks,
                resolved: currentResolved,
            };

            const Component = (implementation.tabs as any)[match.tab].component;
            const view = <Component {...componentProps} />;
            return children({
                view,
                tabs,
                locator: currentLocator,
                actions,
                parent,
                options,
            });
        };

        type PreparedTab = {
            name: string;
            locator: Locator;
            isActive: boolean;
        };

        type RenderProps = (props: {
            locator: Locator;
            view: React.ReactNode;
            tabs: PreparedTab[];
            actions: any[];
            parent: Locator | null;
            options: {title: string};
        }) => React.ReactElement;

        const Route = (props: {children: RenderProps}) => {
            const [currentPath, setCurrentPath] = React.useState(location.pathname);
            const [mirror, setMirror] = React.useState(dependencies);

            const match = matchRoutes(routes, currentPath);

            const currentLocator = getLocatorFromURL(currentPath);

            if (match == null || currentLocator == null) {
                return null; // return <div><h1>Invalid route</h1></div>;
            }

            const currentResolved = mirror[currentLocator.scenePath];
            const isLoaded = currentResolved != null;

            React.useEffect(() => {
                const handleResolved = () => setMirror({...dependencies});
                const listener = window.addEventListener("resolved", handleResolved);

                return () => {
                    window.removeEventListener("resolved", handleResolved);
                };
            }, []);

            React.useEffect(() => {
                const onLocationChange = () => {
                    setCurrentPath(location.pathname);
                };
                window.addEventListener("navigate", onLocationChange);

                return () => {
                    window.removeEventListener("navigate", onLocationChange);
                };
            }, []);

            React.useEffect(() => {
                if (isLoaded == false) {
                    (async () => {
                        setResolved({
                            [currentLocator.scenePath]:
                                await currentLocator.routeDefinition.definition.resolve(
                                    {params: currentLocator.params} as any,
                                ),
                        });
                        // setIsLoaded(true);
                    })();
                }
            }, []);

            if (isLoaded == false) {
                return null;
            }

            const implementationForTabs =
                implementations[match.route.name as RouteNames];

            const parentImplementation =
                match.route.definition.parent != null
                    ? implementations[match.route.definition.parent as RouteNames]
                    : null;
            const parentDefinition =
                match.route.definition.parent != null
                    ? routes.find(
                          (route) => route.name == match.route.definition.parent,
                      )
                    : null;

            const parent =
                parentDefinition != null
                    ? locator({
                          ...(currentLocator as any),
                          route: `${parentDefinition.name}.${parentDefinition.definition.tabs[0]}` as any,
                          resolved: currentResolved,
                      })
                    : null;

            return (
                <Loaded
                    currentLocator={currentLocator}
                    match={match}
                    children={props.children}
                    currentResolved={currentResolved}
                    implementation={implementationForTabs}
                    parent={parent}
                />
            );
            /*
            // console.log(implementationForTabs);

            const mounted = routes.map((route) => {
                if (match.route != route) {
                    return null;
                }

                const implementation = implementations[route.name as RouteNames];

                const Component = (implementation.tabs as any)[match.tab].component;
                const camelCase = route.name
                    .toLowerCase()
                    .replace(/([-_][a-z])/g, (group) =>
                        group.toUpperCase().replace("-", "").replace("_", ""),
                    );
                Component.displayName = camelCase[0].toUpperCase() + camelCase.slice(1);

                return (
                    <React.Fragment key={currentLocator.scenePath}>
                        <ResolveProvider>
                            {match != null && match.route == route && (
                                <Loader
                                    locator={currentLocator}
                                    match={match}
                                    hooks={hooks}
                                    component={Component}
                                />
                            )}
                        </ResolveProvider>
                    </React.Fragment>
                );
            });

            return {
                view: mounted,
                options,
                actions,
                parent,
                tabs,
                key: currentLocator.scenePath,
            };
            */
        };

        return {Route};
    };
    return {
        router: {
            reverse,
            push,
        },
        Link,
        mount,
    };
};

export function routeFactory<TGlobalHooks = never>(hooks?: () => TGlobalHooks | false) {
    type WithFalseRemoved = TGlobalHooks extends false ? never : TGlobalHooks;
    type DoesThisWork = TryIt<TGlobalHooks>;

    function route<
        TName extends string,
        TPath extends string,
        TResolve,
        TResolvedSoFar,
        THooks,
        TTabs extends string[] = ["index"],
    >(options: {
        name: TName;
        path: TPath;
        tabs?: [...TTabs];
        resolve?: (props: {params: ExtractRouteParams<TPath>}) => TResolve;
    }): Route<
        TName,
        null,
        TPath,
        TResolve,
        TryIt<TResolve> & TResolvedSoFar,
        WithFalseRemoved,
        THooks,
        TTabs
    > {
        type BoundRouteUsedForTypes = Route<
            TName,
            null,
            TPath,
            TResolve,
            TryIt<TResolve> & TResolvedSoFar,
            WithFalseRemoved,
            THooks,
            TTabs
        >;
        const tabs = options.tabs ?? (["index"] as TTabs);

        const bindWithTab =
            (hooks: any): BoundRouteUsedForTypes["withTab"] =>
            (definition, component) => {
                const tabs: any = {};
                const _withTab: WithTab<any, any, any> = (_definition, _component) => {
                    const tab = {
                        options: {
                            name: _definition.name,
                        },
                        component: _component,
                    };
                    tabs[tab.options.name] = tab;

                    return {
                        withActions: (actions) => {
                            return {
                                actions,
                                options: () => ({title: ""}),
                                tabs,
                                hooks,
                                withOptions: (options) => ({
                                    hooks,
                                    options,
                                    actions,
                                    tabs,
                                }),
                            };
                        },
                        actions: () => [],
                        options: () => ({title: ""}),
                        hooks,
                        tabs,
                        withTab: _withTab,
                    };
                };
                return _withTab(definition, component) as any;
            };

        const bindWithComponent =
            (hooks: any): BoundRouteUsedForTypes["withComponent"] =>
            (component) => {
                const tabs = {
                    index: {
                        options: {
                            name: "index",
                        },
                        component,
                    },
                };
                const options = () => ({title: ""});

                return {
                    hooks,
                    options,
                    actions: () => [],
                    withActions: (actions) => {
                        return {
                            withOptions: (options) => ({
                                hooks,
                                options,
                                actions,
                                tabs,
                            }),
                            hooks,
                            options,
                            actions,
                            tabs,
                        };
                    },
                    tabs,
                };
            };

        return {
            name: options.name,
            subroute: (definition) => {
                const innerResolve = async (props: any) => {
                    const outer = (await options.resolve?.(props)) ?? {};
                    const inner =
                        (await definition.resolve?.({...props, resolved: outer})) ?? {};
                    return {...outer, ...inner};
                };
                const subrouteDefinition = route({
                    ...definition,
                    path: `${options.path}${definition.path}`,
                    resolve: innerResolve,
                }) as any;

                return {
                    ...subrouteDefinition,
                    definition: {
                        ...subrouteDefinition.definition,
                        parent: options.name,
                    },
                };
            },
            withComponent: bindWithComponent({}),
            withTab: bindWithTab({}),
            withHooks: (hooks) => {
                return {
                    withTab: bindWithTab(hooks) as any,
                    withComponent: bindWithComponent(hooks) as any,
                };
            },
            definition: {
                parent: null,
                ...options,
                hooks: (hooks as any) ?? (() => ({})),
                _testing: null as any,
                resolve: options.resolve ?? (() => ({} as TResolve)),
                tabs,
            },
            processed: processRoutePath(options.path, tabs),
        };
    }

    return route;
}

// https://github.com/garronej/tsafe/
// Maybe try this? https://github.com/aleclarson/spec.ts/blob/master/index.d.ts
export function assert<T extends true>() {}
export type Unite<T> = T extends Record<string, unknown>
    ? {[Key in keyof T]: T[Key]}
    : T;

export type StrictEquals<A1, A2> = (<A>() => A extends A2 ? true : false) extends <
    A,
>() => A extends A1 ? true : false
    ? true
    : false;

export type Equals<A1, A2> = StrictEquals<Unite<A1>, Unite<A2>>;

function tests() {
    type ThirdResolve = {
        lastOne: number;
        blah: string;
        foo: string;
    };

    const concat = routeFactory(() => false);

    const first = concat({
        name: "first",
        path: "abc/<string:entry_id>/",
        resolve: ({params}) => ({foo: params.entry_id}),
    });
    const firstPromise = concat({
        name: "firstPromise",
        path: "abc/<string:entry_id>/",
        resolve: ({params}) => Promise.resolve({foo: params.entry_id}),
    });
    // const firstInvalid = concat({path: "abc/<string:entry_id>/", resolve: ({params}) => 3});

    console.log(interpolatePath(first.processed.pattern, {entry_id: 5}));

    firstPromise.definition._testing.resolved;

    const second = firstPromise.subroute({
        name: "second",
        path: "blah/",
        tabs: ["journal", "whatever"],
        resolve: ({params, resolved}) => Promise.resolve({blah: params.entry_id}),
    });

    const third = second.subroute({
        name: "third",
        path: "finally/<number:test>/",
        resolve: ({params}) => ({lastOne: params.test}),
    });

    assert<Equals<ThirdResolve, typeof third.definition._testing.resolved>>();
    assert<Equals<"third", typeof third.name>>();
    assert<Equals<["journal", "whatever"], typeof second.definition.tabs>>();

    const noGlobalHooks = routeFactory()({name: "", path: ""});
    assert<Equals<never, typeof noGlobalHooks.definition._testing.hooks>>();

    const globalHooks = routeFactory(() => ({profile: "my profile"}))({
        name: "",
        path: "",
    });
    assert<Equals<{profile: string}, typeof globalHooks.definition._testing.hooks>>();

    const cannotLoadHook = routeFactory(() => false)({name: "", path: ""});
    assert<Equals<never, typeof cannotLoadHook.definition._testing.hooks>>();

    routeFactory()({
        name: "first_level_deps",
        path: "",
        resolve: ({params}) => {
            assert<Equals<{}, typeof params>>();
            return Promise.resolve({
                something: 5,
            });
        },
    }).withComponent((props) => {
        assert<Equals<{something: number}, typeof props.resolved>>();
        return <></>;
    });

    routeFactory()({
        name: "first_level_no_resolve",
        path: "",
    }).withComponent((props) => {
        // assert<Equals<unknown, typeof props.resolved>>();
        assert<Equals<RemoveNulls<unknown>, typeof props.resolved>>();
        return <></>;
    });

    // This should fail.
    routeFactory()({
        name: "first_level_wrong_resolve",
        path: "",
        resolve: ({params}) => {
            return Promise.resolve(5);
        },
    }).withComponent((props) => {
        assert<Equals<number, typeof props.resolved>>();
        return <></>;
    });

    routeFactory()({
        name: "first_level",
        path: "first-part/<string:first>/",
        resolve: (props) => {
            const {params} = props;

            // @ts-expect-error
            props.resolved;

            assert<Equals<{first: string}, typeof params>>();

            return Promise.resolve({
                firstResolve: params.first,
            });
        },
    })
        .subroute({
            name: "second_level",
            path: "second-part/<number:second>/",
            resolve: ({params, resolved}) => {
                assert<Equals<{first: string; second: number}, typeof params>>();
                assert<Equals<{firstResolve: string}, typeof resolved>>();

                return {
                    secondResolve: {
                        dependencyOnTheFirstResolve: resolved.firstResolve,
                        somethingHere: params.second,
                    },
                };
            },
        })
        .withComponent((props) => {
            type Resolved = {
                secondResolve: {
                    dependencyOnTheFirstResolve: string;
                    somethingHere: number;
                };
            } & {
                firstResolve: string;
            };
            assert<Equals<Resolved, typeof props.resolved>>();
            return <></>;
        });
}
// tests();

const pageVariants = {
    initial: {
        opacity: 0,
        x: "-100%",
        scale: 0.8,
    },
    in: {
        opacity: 1,
        x: 0,
        scale: 1,
    },
    out: {
        opacity: 0,
        x: "100%",
        scale: 1.2,
    },
};

const pageTransition = {
    type: "tween",
    ease: "anticipate",
    duration: 0.5,
};
