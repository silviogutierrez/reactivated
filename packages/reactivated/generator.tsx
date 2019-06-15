import {Project, StructureKind} from "ts-morph";

const project = new Project();

interface First {
    name: 'foo';
    args: {
        uuid: string;
    }
}

interface Second {
    name: 'bar';
    args: {
        pk: number;
    }
}

interface Third {
    name: 'spam';
}

interface Fourth {
    name: 'ham';
}

type WithArguments = First|Second;
type WithoutArguments = Third|Fourth;
type All = WithArguments|WithoutArguments;
type UnionKeys<T> = T extends any ? keyof T : never
type DistributivePick<T, K extends UnionKeys<T>> = T extends any ? Pick<T, Extract<keyof T, K>> : never;


function reverse<T extends WithoutArguments['name']>(name: T): void;
function reverse<T extends WithArguments['name']>(name: T, args: Extract<WithArguments, {name: T}>['args']): void;
function reverse<T extends All['name']>(name: T, args?: Extract<WithArguments, {name: T}>['args']): void {
}

reverse('foo', {uuid: 'a'});
reverse('bar', {pk: 1});
reverse('spam');
reverse('ham');


const myEnumFile = project.createSourceFile("src/MyEnum.ts", {
    statements: [{
        kind: StructureKind.Enum,
        name: "MyEnum",
        isExported: true,
        members: [{ name: "member" }]
    }, ]
});


project.save();