var Input = function( tr, parentId, submitFunc )
{
	var input = this;

	this.TR = tr;
	this.IsRoot = !parentId;
	this.ParentId = parentId;
	this.SubmitFunc = submitFunc;

	this.Draw = function()
	{
		this.TR.html( '<td class="ubbbtns" width="150px"></td><td class="tpctd"> \
			<textarea name="article" rows="16" cols="100" style="overflow:auto; width:98%;" \
			 placeholder="在此输入帖子内容。第一行为标题。"></textarea><br/><button> 提 交 </button> \
			 <div class="note"/></td>' );

		if( this.IsRoot )
		{
			$( 'button', this.TR ).before( '<select><option value=0>永久保存</option> \
				<option value=10>保存 10 日</option><option value=50>保存 50 日</option> \
				<option value=200>保存 200 日</option><option value=1000>保存 1000 日</option> \
				</select><input type="text" placeholder="在此输入标签，用逗号分隔。不能为空。"/>' );
		}

		$( 'button', this.TR ).click( function()
		{
			$( '.note', input.TR ).html( '' );

			var Content = $( 'textarea', input.TR ).val();
			Content = _( Content.split( '\n' )).chain().map( function( ln )
			{
				return ln.replace( /^\s+|\s+$/g, '' );
			} ).filter( function( ln )
			{
				return ln > '';
			} ).value().join( '\n\n' );

			if( input.IsRoot )
			{
				if( Content.length < 20 )
				{
					$( '.note', input.TR ).html( '根帖内容不能少于 20 字。' );
					return;
				}

				var AtclLabels = $( ':text', input.TR ).val()

				//console.log( AtclLabels );
				if( !AtclLabels )
				{
					$( '.note', input.TR ).html( '标签不能为空。' );
					return;
				}

				var AtclData = {
					'cmd': 'NewTopic',
					'content': Content,
					'Labels': AtclLabels,
					'life': 86400000 * $( '.tpctd>select' ).children( 'option:selected' ).val(),
								};
			}
			else
			{
				if( Content.length < 1 )
				{
					$( '.note', input.TR ).html( '帖子不能为空。' );
					return;
				}

				var AtclData = {
					'cmd': 'Reply',
					'parent': input.ParentId,
					'content': Content,
								};
			}
			console.log( AtclData );

			input.SubmitFunc( AtclData );
		} );
	};

	this.Draw();
};


var Forum = function( owner )
{
	var frm = this;

	this.FLOWMODE = 0;
	this.LINKMODE = 1;
	this.STARMODE = 2;

	this.Owner = owner;
	this.StartPos = 0;
	this.ListLabel = '';
	this.SortCol = 'LastTime';
	this.TopicObj = {};

	this.Init = function()
	{
		$( '#newtpcbtn' ).click( function()
		{
			//alert( 'ssssss' );
			$( '#tpcinput' ).toggle( 350 );
		} );

		$( '.tpctd>button' ).click( function()
		{
			//console.log( 'newtopic' );
			var Content = $( '.tpctd>textarea' ).val()
			if( Content.length < 20 )
			{
				$( '.tpctd>.note' ).html( '帖子内容不能少于 20 字。' );
				return;
			}

			var AtclLabels = $( '.tpctd>:text' ).val()

			//console.log( AtclLabels );
			if( !AtclLabels )
			{
				$( '.tpctd>.note' ).html( '标签不能为空。' );
				return;
			}

			$( '.tpctd>.note' ).html( '' );

			var TopicData = {
				'cmd': 'NewTopic',
				'content': Content,
				'Labels': AtclLabels,
				'life': 86400000 * $( '.tpctd>select' ).children( 'option:selected' ).val(),
			};

			console.log( TopicData );

			frm.Owner.Post( TopicData, 'GetResult' );
		} );

		$( '#firstth' ).click( function()
		{
			frm.SortCol = 'FirstTime';
			frm.StartPos = 0;
			$( '#lastth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#lastth' ).click( function()
		{
			frm.SortCol = 'LastTime';
			frm.StartPos = 0;
			$( '#firstth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#returntolist' ).click( function()
		{
			$( '#atclpg' ).hide( 200 );
			$( '#listpg' ).show( 300 );
		} );
	};

	this.SetClickTitle = function( dom )
	{
		$( 'span.title', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			//console.log( Root );
			frm.Owner.Post( { cmd: 'GetAtclTree', root: Root, mode: 'flow' }, 'GetResult' );
		} );
	};

	this.SetClickLastTime = function( dom )
	{
		$( 'span.lasttime', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			//console.log( Root );
			frm.Owner.Post( { cmd: 'GetAtclTree', root: Root, mode: 'last' }, 'GetResult' );
		} );
	};
	
	this.SetClickArrow = function( dom )
	{
		$( 'span.arrow', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			if( $( this ).text() == '◣' )
			{
				frm.Owner.Post( { cmd: 'GetAtclTree', root: Root, mode: 'tree' }, 'GetResult' );
				$( this ).html( '◤' );
				$( this ).attr( 'title', '降维' );
			}
			else
			{
				$( '#Tree_' + Root ).hide( 400, function()
					{
						$( this ).remove();
					} );
				$( this ).html( '◣' );
				$( this ).attr( 'title', '升维' );
			}
		} );
	};

	this.SetAttr = function( dom )
	{
		this.SetClickTitle( dom );
		this.SetClickLastTime( dom );
		this.SetClickArrow( dom );

		setTimeout( function(){ dom.removeClass( 'new' ); }, 2000 );
	};
	
	this.ShowContent = function( c )
	{
		return c.replace( /\&/g, '&amp;' ).replace( /\>/g, '&gt;' ).replace( /\</g, '&lt;' ).replace( /\n/g, '<br/>' );
	};

	this.ShowSingleAtcl = function( atclData )
	{
		console.log( atclData );
		var AtclDiv = $( '<div class="atcl" id="Atcl_' + atclData[0] + '"><table><tbody><tr> \
			<td class="atclleft"><div class="nickname"></div> \
			<div class="randomart" title="不同用户可能有相同的用户名，\n可通过 RandomArt 识别用户。"></div> \
			<div class="manageuser"></div></td><td class="atclright"><div class="atcltop"> \
			<span class="time"></span><span class="atclid"></span><span class="lineright"> \
			<span class="bigger" title="放大帖子正文">大</span><span class="smaller" title="缩小帖子正文">小</span> \
			</span></div><div class="atclbody"></div> \
			<div class="atclfoot"><span class="manage">zzzzzzzzzzzzz</span><span class="lineright"> \
			<!--button class="like">赞<span class="likenum"></span></button--> \
			<button class="reply">回复</button></span></div> \
			</td></tr></tbody></table><div></div></div>' );

		var AuthPubKey = atclData[1][0].AuthPubKey;
		var AuthStatus = frm.Owner.ChkAuthStatus( AuthPubKey );
		var NameDiv = $( '.nickname', AtclDiv );

		NameDiv.html( atclData[1][0].NickName );
		NameDiv.attr( 'title', '用户公钥：' + AuthPubKey );

		if( AuthStatus >= 0 )
		{
			$( '.atclbody', AtclDiv ).html( frm.ShowContent( atclData[1][1] ));
		}
		else
		{
			$( '.atclbody', AtclDiv ).html( '因用户被屏蔽内容不可见。<button>点此查看</button>' );
			$( '.atclbody>button', AtclDiv ).click( function()
			{
				$( this ).parent().html( frm.ShowContent( atclData[1][1] ));
			} );
		}
		
		$( '.randomart', AtclDiv ).html( frm.RandomArt( str_md5( AuthPubKey )));
		$( '.manageuser', AtclDiv ).append( AuthStatus >= 0 ? '<button class="blockbtn">屏蔽</button>' : '<button class="unblockbtn">解除屏蔽</button>' );
		$( '.manageuser', AtclDiv ).append( AuthStatus <= 0 ? '<button class="followbtn">关注</button>' : '<button class="unfollowbtn">取消关注</button>' );
		$( '.time', AtclDiv ).html( frm.ShowTime( atclData[1][0].CreateTime ));
		$( '.atclid', AtclDiv ).html( '&nbsp;' + atclData[0] );
		//$( '.likenum', AtclDiv ).html(( atclData[1][0].Liked || [] ).length );
		$( '.atclfoot', AtclDiv ).data( 'atclid', atclData[0] );

		return AtclDiv;
	};

	var SetSize = function()
	{
		var Body = $( this ).closest( 'td' ).children( '.atclbody' );
		var size = parseFloat( Body.css( "font-size" ), 10 );
		var diff = $( this ).hasClass( 'bigger' ) ? 2: -2;
		size += diff;
		Body.css( "font-size", size + 'px' );
		Body.css( "line-height", size * 1.5 + "px" );				
	};

	var EnableReply = function()
	{
		var TBody = $( this ).closest( 'tbody' );
		if( TBody.children( 'tr.input' ).length > 0 )
		{
			TBody.children( 'tr.input' ).toggle( 300 );
			return;
		}
		var TR = $( '<tr class="input"></tr>' );
		console.log( $( this ).closest( '.atclfoot' ).data( 'atclid' ));
		new Input( TR, $( this ).closest( '.atclfoot' ).data( 'atclid' ), function( data )
		{
			data.root = $( '#atclarea' ).data( 'root' );
			frm.Owner.Post( data, 'GetResult' );
		} );

		TR.hide();
		TBody.append( TR );
		TR.show( 400 );
	};

	this.SetTopicData = function( treeData )
	{
		var Tree = this.TopicObj[treeData[0]] = _( treeData[1] ).omit( function( v )
		{
			return v[0].Type == 1;
			/*if( v[0].Type == 1 )
			{
				console.log( k, v[0].ParentID ); 
				var Parent = treeData[1][v[0].ParentID];

				Parent[0].Liked = Parent[0].Liked || [];
				Parent[0].Liked.push( v[0].AuthPubKey );
				console.log( Parent[0].Liked )
				return true;
			}
			return false;*/
		} );

		var Roots = [treeData[0]];

		_( Tree ).chain().pairs().sortBy( function( p )
		{
			return p[1][0].CreateTime;
		} ).each( function( p )
		{
			var ParentId = p[1][0].ParentID;
			if( !ParentId )
			{
				return;
			}
			var Parent = Tree[ParentId]
			if( Parent )
			{
				Parent[0].Children = Parent[0].Children || [];
				Parent[0].Children.push( p[0] );
			}
			else
			{
				Roots.push( ParentId );
			}
		} );

		Tree.Roots = Roots;
	};

	this.FlowModeAtcls = function( rootId )
	{
		return _( this.TopicObj[rootId] ).chain().pairs().sortBy( function( p )
				{
					return p[1][0].CreateTime;
				} );
	};

	this.LinkModeAtcls = function( rootId, atclId )
	{
		var Topic = this.TopicObj[rootId];
		var Atcl = Topic[atclId]
		var Atcls = [];

		while( Atcl )
		{
			Atcls.push( [atclId, Atcl] );
			atclId = Atcl[0].ParentID;
			Atcl = Topic[atclId]
		}

		return _( Atcls ).chain().reverse();
	};

	this.StarModeAtcls = function( rootId, atclId )
	{
		var Topic = this.TopicObj[rootId];
		var Atcls = [[atclId, Topic[atclId]]];
		var start = 0;
		var end = 1;

		while( start < end )
		{
			console.log( start, end );
			_( Atcls.slice( start, end )).each( function( parent )
			{
				_( parent[1][0].Children || [] ).each( function( ch )
				{
					var Child = Topic[ch];
					if( Child )
					{
						Atcls.push( [ch, Child] );
					}
				} );
			} );
			start = end;
			end = Atcls.length;
		}
		return _( Atcls );
	};

	this.ShowAtcls = function( rootId, mode, atclId )
	{
		$( '#listpg' ).hide( 200 );
		$( '#atclpg' ).show( 300 );
		$( '#atclarea' ).html( '' );
		$( '#atclarea' ).data( 'root', rootId );
		
		var Atcls = this[[
				'FlowModeAtcls', 
				'LinkModeAtcls', 
				'StarModeAtcls',
					][mode]]( rootId, atclId );

		Atcls.each( function( p )
		{
			console.log( p );
			$( '#atclarea' ).append( frm.ShowSingleAtcl( p ));
		} );

		$( '#atclarea .atcltop>.lineright>span' ).click( SetSize );

		$( '#atclarea .reply' ).click( EnableReply );

		/*$( '.like' ).click( function()
		{
			//console.log( Tree );
			var AuthPubK = frm.Owner.CurUser[0];
			var AtclId = $( this ).closest( '.atclfoot' ).data( 'atclid' );
			var Atcl = Tree[AtclId]

			//console.log( AuthPubK, Atcl );
			if( AuthPubK == Atcl[0].AuthPubKey )
			{
				alert( '不能给自己的帖子点赞。' );
				return;
			}
			if( _( Atcl[0].Liked ).contains( AuthPubK ))
			{
				alert( '不能重复点赞。' );
				return;
			}

			frm.Owner.Post( { cmd: 'Like', atclId: AtclId, root: treeData[0] }, 'GetResult' );
		} );*/
	};

	/*this.AddLike = function( newLike )
	{
		var ParentId = 'Atcl_' + newLike[0].ParentID;
		var LikeNum = $( '#' + ParentId + ' .likenum' );
		LikeNum.html( Number( LikeNum.html()) + 1 );
	};*/

	this.SetClickTreeTitle = function( root, TR )
	{
		console.log( 'SetClickTreeTitle' );
		var AtclId = TR.data( 'atclid' );
		$( '.title', TR ).click( function()
		{
			frm.ShowAtcls( root, frm.STARMODE, AtclId );
		} );
	};

	this.SetClickTreeLastTime = function( root, TR )
	{
		console.log( 'SetClickTreeLastTime' );
		var AtclId = TR.data( 'atclid' );
		$( 'td:eq(4)', TR ).click( function()
		{
			frm.ShowAtcls( root, frm.LINKMODE, AtclId );
		} );
	};

	this.SetClickTreeArrow = function( root, TR )
	{
		console.log( 'SetClickTreeArrow' );
		var AtclId = TR.data( 'atclid' );
		var Atcl = this.TopicObj[root][AtclId];

		$( '.arrow', TR ).click( function()
		{
			if( $( this ).text() == '◣' )
			{
				var AppendAtcl = $( '<tr id="Append_' + AtclId + '"><td colspan=5></td></tr>' );

				AppendAtcl.children( 'td' ).append( frm.ShowSingleAtcl( [AtclId, Atcl] ));
				$( '.atcltop>.lineright>span', AppendAtcl ).click( SetSize );
				$( '.reply', AppendAtcl ).click( EnableReply );

				TR.after( AppendAtcl );
				$( this ).html( '◤' );
				$( this ).attr( 'title', '降维' );
			}
			else
			{
				$( '#Append_' + AtclId ).hide( 400, function()
					{
						$( this ).remove();
					} );
				$( this ).html( '◣' );
				$( this ).attr( 'title', '升维' );
			}
		} );
	};

	this.SetTreeLineAttr = function( root, trLnTR )
	{
		this.SetClickTreeTitle( root, trLnTR );
		this.SetClickTreeLastTime( root, trLnTR );
		this.SetClickTreeArrow( root, trLnTR );		
	};

	this.ShowTree = function( rootId )
	{
		console.log( 'ShowTree' );
		var TR = $( '<tr id="Tree_' + rootId + '"><td colspan=4><table><tbody></tbody></table></td></tr>' );

		_( this.TopicObj[rootId].Roots ).each( function( r )
		{
			frm.DrawTreeLine( rootId, r, $( 'tbody', TR ), 0 );
		} );

		$( 'tr', TR ).each( function()
		{
			frm.SetTreeLineAttr( rootId, $( this ));
		} );

		return TR;
	};

	this.DrawTreeLine = function( rootId, parentId, tbody, layer )
	{
		//console.log( rootId, parentId, layer );
		var Parent = this.TopicObj[rootId][parentId];
		if( !Parent )
		{
			return;
		}
		//console.log( Parent );
		var TreeLine = $( '<tr class="treeview"><td><span class="arrow">◣</span></td><td></td><td></td><td></td><td></td></tr>' );
		TreeLine.data( 'atclid', parentId );
		TreeLine.children( 'td:eq(1)' ).css( 'padding-left', ( layer * 7 ) + 'px' );
		var Prefix = rootId == parentId ? '●' : layer == 0 ? '◇' : '◆';
		TreeLine.children( 'td:eq(1)' ).html( Prefix + '<span class="title">' + Parent[1].slice( 0, 99 ) + '</span>' );
		TreeLine.children( 'td:eq(2)' ).html( Parent[0].NickName );
		TreeLine.children( 'td:eq(3)' ).html( Parent[1].length + '字' );
		TreeLine.children( 'td:eq(4)' ).html( this.ShowTime( Parent[0].CreateTime ));
		tbody.append( TreeLine );
		_( Parent[0].Children || [] ).chain().reverse().each( function( childId )
		{
			frm.DrawTreeLine( rootId, childId, tbody, layer + 1 );
		} );
	};

	this.ReplyOK = function( replyData )
	{
		console.log( replyData );
		var ParentId = 'Atcl_' + replyData[1][0].ParentID;
		var Parent = $( '#' + ParentId );
		var NewAtcl = this.ShowSingleAtcl( replyData );
		$( '.atcltop>.lineright>span', NewAtcl ).click( SetSize );
		$( '.reply', NewAtcl ).click( EnableReply );
		NewAtcl.hide();
		Parent.after( NewAtcl );
		NewAtcl.show( 400 );
		$( '.input', Parent ).hide( 300 );
	}

	this.RandomArt = function( data )
	{
		var Bound = [
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					];

		var x = 8;
		var y = 4;

		Bound[y][x] = -1;

		_( data ).each( function( c )
		{
			var Byte = c.charCodeAt();
			for( var i = 0; i < 4; i++ )
			{
				if( Byte & 0x01 && x < 16 )
				{
					x++;
				}
				else if( !( Byte & 0x01 ) && x > 0 )
				{
					x--;
				}

				if( Byte & 0x02 && y < 8 )
				{
					y++;
				}
				else if( !( Byte & 0x02 ) && y > 0 )
				{
					y--;
				}

				if( Bound[y][x] >= 0 )
				{
					Bound[y][x]++;
				}
				
				Byte >>= 2;
			}
		} );

		Bound[y][x] = -2;

		var s = '';
		_( Bound ).each( function( ln )
		{
			_( ln ).each( function( n )
			{
				s += n >= 0 ? ' .o+=*BOX@%&#/^QMZ'[n] : 'ES'[n + 2];
			} );
			s += '<br/>'
		} );

		return s.replace( / /g, '&nbsp;' );
	};

	this.GetNextPage = function()
	{
		var Param = {
			'cmd': 'GetTpcList',
			'start': this.StartPos,
			'label': this.ListLabel,
			'sortby': this.SortCol,
					};
		//console.log( Param );

		if( this.StartPos == 0 )
		{
			$( '#tpclist>table>tbody>tr:gt(0)' ).remove();
		}

		frm.Owner.Post( Param, 'GetResult' );
	};

	this.FillZero = function( s )
	{
		return ( '00' + s ).slice( -2 );
	};

	this.ShowTime = function( intTime, onlyDate )
	{
		var d = new Date();
		d.setTime( intTime );
		if( onlyDate )
		{
			return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate());
		}
		return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate()) + ' '
				+ this.FillZero( d.getHours()) + ':' + this.FillZero( d.getMinutes()) + ':' + this.FillZero( d.getSeconds());
	};

	this.TopicTR = function( tpcdata )
	{
		var TR = $( '<tr class="new" id="Topic_' + tpcdata[0] + '"><td class="title"></td> \
			<td class="first"></td><td class="num">1</td><td class="last"></td></tr>' );
		var LabelSpans = _( tpcdata[2].split( ',' )).chain().map( function( lb )
			{
				return '<span class="tpclabel">' + lb + '</span>';
			} ).value().join( '' );
		//console.log( LabelSpans );
		var Title = '<span class="arrow" title="升维">◣</span><span class="title" title="进入话题">' + tpcdata[1] + '</span>' + LabelSpans;
		TR.children( 'td:eq(0)' ).html( Title )
		TR.children( 'td:eq(1)' ).html( tpcdata[5] + '<br><span class="firsttime">' + this.ShowTime( tpcdata[6], true ) + '</span>' );
		TR.children( 'td:eq(2)' ).html( tpcdata[4] )
		TR.children( 'td:eq(3)' ).html( '<span class="lasttime" title="查看更新">' + this.ShowTime( tpcdata[8] ) + '</span><br>' + tpcdata[7] );
		TR.data( 'root', tpcdata[0] );

		return TR;
	};

	this.Init();
}