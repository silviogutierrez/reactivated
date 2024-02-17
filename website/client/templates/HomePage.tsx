import React from "react";

import {templates} from "@reactivated";
import {Helmet} from "react-helmet-async";

import outdent from "outdent";

import {Code} from "@client/components/Code";
import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";
import * as styles from "@client/styles.css";

const Highlight = (props: JSX.IntrinsicElements["div"]) => (
    <div {...props} className={styles.Highlight} />
);

const InstallationCommand = (props: JSX.IntrinsicElements["pre"]) => (
    <pre {...props} className={styles.InstallationCommand} />
);

const Links = (props: JSX.IntrinsicElements["ul"]) => (
    <ul {...props} className={styles.Links} />
);

const Site = (props: {title: string; children: React.ReactNode}) => (
    <Layout title={props.title}>
        <div>
            <main
                style={{
                    display: "flex",
                    flexDirection: "column",
                    flex: 1,
                    gap: 30,
                }}
            >
                {props.children}
            </main>
            <footer
                style={{
                    textAlign: "center",
                    fontSize: 15,
                    padding: 20,
                }}
            >
                <p>
                    A{" "}
                    <a target="_blank" href="https://www.silv.io" rel="noreferrer">
                        Silvio Gutierrez
                    </a>{" "}
                    Initiative
                </p>
            </footer>
        </div>
    </Layout>
);

const Star = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        focusable="false"
        fill="currentColor"
        width={16}
        height={16}
    >
        <path d="M23 9c-.1-.4-.4-.6-.8-.7l-6.4-.9-2.9-5.8c-.3-.7-1.5-.7-1.8 0L8.2 7.3l-6.3 1c-.4 0-.7.3-.9.7-.1.4 0 .8.3 1l4.6 4.5-1.1 6.4c-.1.4.1.8.4 1 .2 0 .4.1.6.1.2 0 .3 0 .5-.1l5.7-3 5.7 3c.3.2.7.1 1.1-.1.3-.2.5-.6.4-1l-1.1-6.4 4.6-4.5c.3-.2.4-.6.3-.9zm-6.7 4.4c-.2.2-.3.6-.3.9l.8 4.9-4.4-2.3c-.3-.2-.6-.2-.9 0l-4.4 2.3.9-4.9c0-.3-.1-.7-.3-.9L4.1 10 9 9.3c.3 0 .6-.3.8-.5L12 4.3l2.2 4.4c.1.3.4.5.8.5l4.9.7-3.6 3.5z" />
    </svg>
);

const GitHub = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={24}
        height={24}
        viewBox="0 0 24 24"
        focusable="false"
        fill="currentColor"
    >
        <path
            d="M12.006 2a10 10 0 00-3.16 19.489c.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.341-3.369-1.341a2.648 2.648 0 00-1.11-1.463c-.908-.62.068-.608.068-.608a2.1 2.1 0 011.532 1.03 2.13 2.13 0 002.91.831 2.137 2.137 0 01.635-1.336c-2.22-.253-4.555-1.11-4.555-4.943a3.865 3.865 0 011.03-2.683 3.597 3.597 0 01.098-2.647s.84-.269 2.75 1.026a9.478 9.478 0 015.007 0c1.909-1.294 2.747-1.026 2.747-1.026a3.592 3.592 0 01.1 2.647 3.859 3.859 0 011.027 2.683c0 3.842-2.338 4.687-4.566 4.935a2.387 2.387 0 01.68 1.852c0 1.336-.013 2.415-.013 2.743 0 .267.18.578.688.48A10.001 10.001 0 0012.006 2z"
            fillRule="evenodd"
        />
    </svg>
);

const DOCKER = `
    window.addEventListener('DOMContentLoaded', () => {
        document.getElementById("docker").onclick = (event) => {
            event.preventDefault();
            document.getElementById("docker-command").style.display = ""
            document.getElementById("docker-option").style.display = "none"
            document.getElementById("nix-command").style.display = "none"
            document.getElementById("docker-warning").style.display = ""
        };
    });
`;

export const Template = (props: templates.HomePage) => (
    <Site title="Reactivated — Zero-configuration Django and React">
        <Helmet>
            <script>{DOCKER}</script>
        </Helmet>
        <div
            style={{
                backgroundColor: styles.colors.background,
            }}
        >
            <div className={styles.homePageHeader}>
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 30,
                    }}
                >
                    <h1 style={{fontSize: 32}}>
                        Zero-configuration Django and React.
                        <br />
                        Together at last.
                    </h1>
                    <div
                        style={{
                            fontSize: 18,
                            display: "flex",
                            flexDirection: "column",
                            gap: 20,
                        }}
                    >
                        <p>
                            Reactivated is the easiest way to use Django and React
                            together.
                        </p>
                        <p>
                            You get the full power of Django. Rendered by React{" "}
                            <strong>server-side</strong>.
                        </p>
                        <p>No webpack, no config, no tooling. Just React and Django.</p>
                    </div>
                    <InstallationCommand id="nix-command">
                        nix-shell -E &quot;$(curl -L
                        https://reactivated.io/install/)&quot;
                    </InstallationCommand>
                    <InstallationCommand
                        id="docker-command"
                        style={{display: "none", fontSize: 13.5}}
                    >
                        {outdent`
                        docker run -itv $PWD:/app silviogutierrez/reactivated install my_app
                        `}
                    </InstallationCommand>
                    <div className={styles.homePageButtons}>
                        <forms.ButtonLink href="/documentation/getting-started/">
                            Get Started
                        </forms.ButtonLink>
                        <forms.ButtonLink
                            style={{
                                gap: 10,
                            }}
                            href="https://github.com/silviogutierrez/reactivated"
                        >
                            <GitHub />
                            <span
                                style={{
                                    display: "flex",
                                    gap: 5,
                                }}
                            >
                                <Star />
                                {props.stars}
                            </span>
                        </forms.ButtonLink>
                        <forms.ButtonLink
                            className={styles.hideOnMobile}
                            href="https://nixos.org/download.html"
                        >
                            Install Nix
                        </forms.ButtonLink>
                    </div>
                    <p id="docker-option" style={{marginTop: -20}}>
                        Don‘t have Nix?{" "}
                        <a id="docker" href="#">
                            Use Docker
                        </a>
                    </p>
                    <p id="docker-warning" style={{marginTop: -20, display: "none"}}>
                        But you really should be{" "}
                        <a href="/documentation/why-nix/">using Nix</a>.
                    </p>
                </div>
                <div
                    style={{
                        flex: 1,
                        display: "flex",
                        flexDirection: "column",
                        gap: 15,
                    }}
                >
                    <Code language="python">
                        {outdent`
                            from django.http import HttpRequest, HttpResponse
                            from django.shortcuts import redirect

                            from . import forms, templates

                            def home_page(request: HttpRequest) -> HttpResponse:
                                form = forms.SignUpForm(request.POST or None)
                                if form.is_valid():
                                    form.save()
                                    return redirect("profile")

                                return templates.HomePage(form=form).render(request)
                        `}
                    </Code>
                    <Code language="tsx">
                        {outdent`
                            import React from "react";
                            import {CSRFToken, Form, templates} from "@reactivated";

                            import {Layout} from "@client/components/Layout";

                            export default (props: templates.HomePage) => (
                                <Layout title="Sign Up">
                                    <h1>Sign Up</h1>
                                    <form method="POST">
                                        <CSRFToken />
                                        <Form as="p" form={props.form} />
                                        <button type="submit">Submit</button>
                                    </form>
                                </Layout>
                            );
                        `}
                    </Code>
                </div>
            </div>
        </div>
        <div>
            <div
                style={{
                    margin: "0 auto",
                    maxWidth: 1200,
                    paddingLeft: 20,
                    paddingRight: 20,

                    display: "flex",
                    flexDirection: "column",
                    gap: 40,
                }}
            >
                <div className={styles.homePageFeatures}>
                    <div>
                        <h2>Type Safe</h2>
                        <p>TypeScript and Mypy built-in. Catch mistakes early.</p>
                    </div>
                    <div>
                        <h2>Deployment Ready</h2>
                        <p>
                            Run one command and have your app live with production
                            settings. SSL included.
                        </p>
                    </div>
                    <div>
                        <h2>No Dependencies</h2>
                        <p>
                            Ok just one. <strong>Nix</strong>. Everything is included
                            and set up for you.
                        </p>
                    </div>
                    <div>
                        <h2>Opinionated</h2>
                        <p>
                            Formatting and linting configured for you. One command to
                            fix it all.
                        </p>
                    </div>
                </div>
                <hr />
                <div
                    style={{
                        textAlign: "center",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: 15,
                        fontSize: 17,
                    }}
                >
                    <h2>The full power of Django</h2>
                    <p>
                        Nothing — that’s right, <em>nothing</em> — approaches the
                        productivity of a mature framework like Django.
                    </p>
                    <p>
                        So why cripple its vast feature set by separating the frontend
                        from the backend? REST calls and ad-hoc endpoints is no way to
                        live.
                    </p>
                    <p>
                        Use idiomatic Django. As it was meant to be used: with forms,
                        form sets, views and transactional logic.
                    </p>
                    <Code language="python">
                        {outdent`
                            @transaction.atomic
                            def checkout(request: HttpRequest) -> HttpResponse:
                                registration_form = forms.RegistrationForm(request.POST or None)
                                credit_card_form = forms.CreditCardForm(request.POST or None)
                                cart_form_set = forms.CardFormSet(request.POST or None)

                                if (
                                    registration_form.is_valid()
                                    and credit_card_form.is_valid()
                                    and cart_form_set.is_valid()
                                ):
                                    user = registration_form.save(commit=False)
                                    user.credit_card = credit_card_form.save()
                                    user.save()

                                    for item in cart_form_set.save(commit=False):
                                        item.user = user
                                        item.save()
                                    return redirect("order_history")

                                return templates.Checkout(
                                    registration_form=registration_form,
                                    cart_form_set=cart_form_set,
                                    credit_card_form=credit_card_form,
                                ).render(request)
                        `}
                    </Code>
                </div>
                <Highlight>
                    <div>
                        <h2>React is your template engine</h2>
                        <p>Django is great.</p>
                        <p>
                            But writing type-safe components with React is a dream come
                            true.
                        </p>
                        <p>Leverage the full React ecosystem.</p>
                    </div>
                    <Code language="tsx">
                        {outdent`
                            import React from "react";
                            import Select from "react-select";

                            const flavors = [
                                {value: "chocolate", label: "Chocolate"},
                                {value: "strawberry", label: "Strawberry"},
                                {value: "vanilla", label: "Vanilla"},
                            ];

                            export const Flavor = () => <Select options={flavors} />;`}
                    </Code>
                </Highlight>
                <Highlight>
                    <Code language="python">
                        {outdent`
                            class LoginForm(forms.Form):
                                email = forms.EmailField()
                                password = forms.PasswordField()

                            @template
                            class Login(NamedTuple):
                                form: forms.LoginForm
                        `}
                    </Code>
                    <div>
                        <h2>Type safety — everywhere</h2>
                        <p>All roads lead to types. So embrace them.</p>
                        <p>
                            Type your Django code, and all of your React templates will
                            be typed automatically.
                        </p>
                    </div>
                </Highlight>
                <Highlight>
                    <div>
                        <h2>Easily add dynamic behavior</h2>
                        <p>
                            The classic problem. Show a field if a certain value is
                            selected on another field.
                        </p>
                        <p>
                            Tricky with traditional Django. <em>Trivial</em> with
                            Reactivated.
                        </p>
                    </div>
                    <div>
                        <Code language="python">{outdent`
                        class WireForm(forms.Form):
                            account_number = forms.CharField()
                            has_instructions = forms.BooleanField()
                            instructions = forms.TextField()
                    `}</Code>
                        <Code language="tsx">{outdent`
                        import React from "react";

                        import {CSRFToken, useForm, Form} from "@reactivated";

                        export const WireForm = (props: Props) => {
                            const form = useForm(props.form);
                            const fields =
                                form.values.has_instructions === true
                                    ? ["account", "has_instructions", "instructions"]
                                    : ["account", "has_instructions"];

                            return <form method="POST">
                                <CSRFToken />
                                <Form handler={form} as="p" fields={fields} />
                                <button type="submit">Send wire</button>
                            </>;
                        };
                    `}</Code>
                    </div>
                </Highlight>
                <div className={styles.homePageLinks}>
                    <div>
                        <h3>Documentation</h3>
                        <Links>
                            <li>
                                <a href="/documentation/getting-started/">
                                    Getting started
                                </a>
                            </li>
                            <li>
                                <a href="/documentation/existing-projects/">
                                    Existing projects
                                </a>
                            </li>
                        </Links>
                    </div>
                    <div>
                        <h3>Community</h3>
                        <Links>
                            <li>
                                <a href="https://github.com/silviogutierrez/reactivated">
                                    Github
                                </a>
                            </li>
                            <li>
                                <a href="https://github.com/silviogutierrez/reactivated/discussions">
                                    Discussions
                                </a>
                            </li>
                        </Links>
                    </div>
                    <div>
                        <h3>Thoughts</h3>
                        <Links>
                            <li>
                                <a href="/documentation/concepts/">Concepts</a>
                            </li>
                            <li>
                                <a href="/documentation/philosophy-goals/">
                                    Philosophy
                                </a>
                            </li>
                        </Links>
                    </div>
                </div>
            </div>
        </div>
    </Site>
);
