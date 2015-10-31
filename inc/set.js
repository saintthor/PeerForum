var SetItem = function( name, data, setFunc )
{
	var item = this;

	var NameMap = {
			'CurNode': ['本地节点', 'localnode'],
			'CurUser': ['本地用户', 'localuser'],
					};

	this.Draw = function()
	{
		var Choice = $( '<div class="choice" id="' + NameMap[name][1] + '"><div class="title"><span class="trigger">◣</span>'
					 + NameMap[name][0] + '</div><div class="content"><table><tbody></tbody></table>'
					 + '<br><button>提交</button></div></div>' );

		_( data.static ).chain().pairs().each( function( p )
		{
			$( 'tbody', Choice ).append( '<tr><th>' + p[0] + '</th><td>' + p[1] + '</td></tr>' );
		} );
		_( data.variable ).chain().pairs().each( function( p )
		{
			var TR = $( '<tr><th>' + p[0] + '</th><td><input type="text"/></td></tr>' );
			$( ':text', TR ).val( p[1] );
			$( 'tbody', Choice ).append( TR );
		} );

		$( '.content', Choice ).hide();

		Choice.children( '.title' ).click( function()
		{
			var Others = Choice.siblings( '.choice' );
			Others.children( '.content' ).hide( 200 );
			Others.children( '.title' ).children( '.trigger' ).html( '◣' );
			$( this ).children( '.trigger' ).html( '◤' );
			Choice.children( '.content' ).show( 300 );
		} );

		$( 'button', Choice ).click( function()
		{
			setFunc( $( 'tbody', Choice ));
		} );

		$( '#setpg' ).append( Choice );
	};

	this.Draw();

};


var Manager = function( owner )
{
	var manager = this;
	this.Owner = owner;

	
}